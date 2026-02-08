# apps/notificaciones/models.py
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from ..productos.models import Producto
from ..usuario.models import Usuario


class NotificacionBajoStock(models.Model):
    URGENCIA_CHOICES = [
        ('BAJO', 'Bajo'),
        ('URGENTE', 'Urgente'),
        ('CRITICO', 'Crítico'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='notificaciones_stock'
    )
    stock_actual = models.PositiveIntegerField(editable=False, default=0)
    stock_minimo = models.PositiveIntegerField(editable=False, default=0)
    urgencia = models.CharField(max_length=10, choices=URGENCIA_CHOICES, editable=False, default='BAJO')
    mensaje = models.TextField(blank=True, null=True)
    enviada_por_email = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación de Bajo Stock"
        verbose_name_plural = "Notificaciones de Bajo Stock"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['producto']),
            models.Index(fields=['leida']),
            models.Index(fields=['fecha_creacion']),
        ]
        permissions = [
            ("puede_ver_todas_notificaciones", "Puede ver todas las notificaciones"),
        ]

    def __str__(self):
        return f"[{self.get_urgencia_display()}] {self.producto.nombre} - Stock: {self.stock_actual}"

    def save(self, *args, **kwargs):
        """Captura valores del producto al momento de crear la notificación"""
        # Se ejecuta solo al crear una nueva instancia
        if not self.pk:
            self.stock_actual = self.producto.stock_actual
            self.stock_minimo = self.producto.stock_minimo
            self.urgencia = self.calcular_urgencia()
            if not self.mensaje:
                self.mensaje = self.generar_mensaje_automatico()
        
        super().save(*args, **kwargs)

    def calcular_urgencia(self):
        """Calcula la urgencia según el stock actual vs mínimo"""
        if self.producto.stock_actual == 0:
            return 'CRITICO'
        elif self.producto.stock_actual <= self.producto.stock_minimo / 2:
            return 'URGENTE'
        return 'BAJO'

    def generar_mensaje_automatico(self):
        """Genera un mensaje claro, profesional y dinámico"""
        categoria = self.producto.categoria.nombre if self.producto.categoria else "General"
        laboratorio = self.producto.laboratorio.nombre if self.producto.laboratorio else "N/A"
        deficit = max(0, self.stock_minimo - self.stock_actual)
        
        return (
            f"⚠️ REPORTE DE INVENTARIO CRÍTICO\n"
            f"========================================\n"
            f"El producto '{self.producto.nombre}' ha registrado un movimiento que lo sitúa (o mantiene) "
            f"por debajo del nivel de stock mínimo establecido.\n\n"
            f"📊 ESTADO DEL INVENTARIO:\n"
            f"   • Stock Actual:      {self.stock_actual} unidades\n"
            f"   • Mínimo Requerido:  {self.stock_minimo} unidades\n"
            f"   • Déficit a cubrir:  {deficit} unidades\n"
            f"   • Nivel de Urgencia: {self.get_urgencia_display().upper()}\n\n"
            f"📦 FICHA TÉCNICA:\n"
            f"   • Código SKU:  {self.producto.codigo}\n"
            f"   • Categoría:   {categoria}\n"
            f"   • Laboratorio: {laboratorio}\n"
        )

    def enviar_email(self):
        """
        Envía email a admin y farmacéuticos cuando se crea una notificación
        ✅ SE LLAMA AUTOMÁTICAMENTE DESDE save() CUANDO SE CREA LA NOTIFICACIÓN
        """
        # ✅ VERIFICAR QUE NO SE HAYA ENVIADO YA
        if self.enviada_por_email:
            print(f"⚠️ Email ya enviado para notificación {self.id}")
            return False

        # ✅ OBTENER DESTINATARIOS VÁLIDOS
        destinatarios = Usuario.objects.filter(
            rol__in=['admin', 'farmaceutico'],
            is_active=True
        ).exclude(
            email__isnull=True
        ).exclude(
            email=''
        ).values_list('email', flat=True)

        if not destinatarios:
            print(f"⚠️ No hay destinatarios con email válido para notificación {self.id}")
            return False

        # ✅ CONFIGURAR ASUNTO SEGÚN URGENCIA
        urgencia_display = self.get_urgencia_display()
        
        # Emojis según urgencia
        emoji = {
            'CRÍTICO': '🔥',
            'URGENTE': '⚠️',
            'BAJO': '📉'
        }.get(urgencia_display, '📊')
        
        subject = f"{emoji} ALERTA DE STOCK: {self.producto.nombre} requiere atención ({urgencia_display})"

        # ✅ CREAR CONTENIDO DEL EMAIL (HTML Y TEXTO PLANO)
        context = {
            'notificacion': self,
            'producto': self.producto,
            'urgencia_display': urgencia_display,
            'fecha': timezone.localtime(self.fecha_creacion).strftime('%d/%m/%Y %H:%M'),
            'stock_restante': self.stock_actual,
            'stock_necesario': self.stock_minimo - self.stock_actual,
            'porcentaje_stock': (self.stock_actual / self.stock_minimo) * 100 if self.stock_minimo > 0 else 0,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        }

        html_message = None
        try:
            # Intenta renderizar la plantilla HTML. Si falla, el email se enviará solo en texto plano.
            html_message = render_to_string('emails/bajo_stock_alert.html', context)
        except Exception as e:
            print(f"⚠️  ADVERTENCIA: No se pudo renderizar la plantilla de email HTML 'emails/bajo_stock_alert.html'. Error: {e}")

        plain_message = f"""
ESTIMADO ADMINISTRADOR / FARMACÉUTICO,

Se ha generado una alerta automática de inventario debido a un movimiento reciente.

{self.mensaje}

--------------------------------------------------
ACCIONES RECOMENDADAS:
1. Verificar el inventario físico.
2. Gestionar la orden de compra o reposición.
3. Actualizar el estado en el sistema.

Acceso directo al producto:
{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/productos/{self.producto.id}

---
Sistema de Gestión de Inventario - Farmacia
        """.strip()

        try:
            # ✅ CONFIGURAR EMAIL FROM
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sistema@farmacia-gym.com')
            
            # ✅ ENVIAR EMAIL
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=list(destinatarios),
                fail_silently=False,
                html_message=html_message,  # Se adjunta si se pudo renderizar
            )
            
            # ✅ MARCAR COMO ENVIADO Y GUARDAR
            self.enviada_por_email = True
            self.save(update_fields=['enviada_por_email'])
            
            # ✅ LOG DE ÉXITO
            print(f"✅ Email enviado correctamente para notificación {self.id}")
            print(f"   Destinatarios: {len(destinatarios)}")
            print(f"   Producto: {self.producto.nombre}")
            print(f"   Urgencia: {urgencia_display}")
            
            return True
            
        except Exception as e:
            # ✅ LOG DE ERROR DETALLADO
            print(f"❌ ERROR enviando email para notificación {self.id}:")
            print(f"   Tipo de error: {type(e).__name__}")
            print(f"   Mensaje: {str(e)}")
            print(f"   From email: {from_email}")
            print(f"   Destinatarios: {list(destinatarios)}")
            
            # ✅ INTENTAR ENVIAR EMAIL SIMPLE (fallback)
            try:
                send_mail(
                    subject=f"[FALLBACK] {subject}",
                    message=f"ALERTA SIMPLE: {self.producto.nombre} - Stock: {self.stock_actual}",
                    from_email=from_email,
                    recipient_list=list(destinatarios),
                    fail_silently=True,
                )
                print(f"   ✅ Email de fallback enviado")
            except Exception as fallback_error:
                print(f"   ❌ Fallback también falló: {fallback_error}")
            
            return False

    # ✅ MÉTODO ADICIONAL PARA REENVIAR EMAIL MANUALMENTE
    def reenviar_email(self):
        """
        Permite reenviar el email manualmente si falló el envío automático
        """
        self.enviada_por_email = False
        self.save(update_fields=['enviada_por_email'])
        return self.enviar_email()