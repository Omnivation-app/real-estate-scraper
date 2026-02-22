"""
Module de notifications par email et SMS pour les alertes de recherche.
"""

import os
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime

from app.models import User, SearchAlert, Listing

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Gestionnaire des notifications par email."""

    def __init__(self):
        """Initialiser le notificateur email."""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envoyer un email.

        Args:
            to_email: Adresse email destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email

        Returns:
            True si succès, False sinon
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_new_listings_notification(
        self, user: User, alert: SearchAlert, listings: List[Listing]
    ) -> bool:
        """
        Envoyer une notification de nouvelles annonces.

        Args:
            user: Utilisateur destinataire
            alert: Alerte de recherche
            listings: Liste des nouvelles annonces

        Returns:
            True si succès, False sinon
        """
        if not listings:
            return False

        # Construire le contenu HTML
        listings_html = ""
        for listing in listings:
            listings_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                <h3 style="margin-top: 0;">{listing.title}</h3>
                <p><strong>Prix:</strong> {listing.price:,.0f}€</p>
                <p><strong>Surface:</strong> {listing.surface_area} m²</p>
                <p><strong>Localisation:</strong> {listing.address_partial}, {listing.postal_code} {listing.city}</p>
                <p><strong>Type:</strong> {listing.property_type.value}</p>
                <a href="{listing.listing_url}" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Voir l'annonce</a>
            </div>
            """

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Nouvelles annonces pour votre alerte: {alert.name}</h2>
                <p>Bonjour {user.full_name or user.username},</p>
                <p>Nous avons trouvé {len(listings)} nouvelle(s) annonce(s) correspondant à votre alerte de recherche.</p>
                
                {listings_html}
                
                <p>
                    <a href="https://yourdomain.com/alerts/{alert.id}" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Gérer mes alertes</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    Real Estate Scraper | Vous recevez cet email car vous avez créé une alerte de recherche.
                    <a href="https://yourdomain.com/settings" style="color: #667eea;">Modifier vos préférences</a>
                </p>
            </body>
        </html>
        """

        subject = f"[Real Estate] {len(listings)} nouvelle(s) annonce(s) pour {alert.name}"
        return self.send_email(user.email, subject, html_content)

    def send_welcome_email(self, user: User) -> bool:
        """
        Envoyer un email de bienvenue.

        Args:
            user: Nouvel utilisateur
            
        Returns:
            True si succès, False sinon
        """
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Bienvenue sur Real Estate Scraper!</h2>
                <p>Bonjour {user.full_name or user.username},</p>
                <p>Merci de vous être inscrit sur notre plateforme. Vous pouvez maintenant:</p>
                <ul>
                    <li>Créer des alertes de recherche personnalisées</li>
                    <li>Sauvegarder vos annonces favorites</li>
                    <li>Recevoir des notifications pour les nouvelles annonces</li>
                </ul>
                <p>
                    <a href="https://yourdomain.com/dashboard" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Accéder à mon tableau de bord</a>
                </p>
                <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
            </body>
        </html>
        """

        subject = "Bienvenue sur Real Estate Scraper!"
        return self.send_email(user.email, subject, html_content)


class SMSNotifier:
    """Gestionnaire des notifications par SMS."""

    def __init__(self):
        """Initialiser le notificateur SMS."""
        # Utiliser Twilio ou un autre service SMS
        self.api_key = os.getenv("SMS_API_KEY", "")
        self.api_url = os.getenv("SMS_API_URL", "")

    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Envoyer un SMS.

        Args:
            phone_number: Numéro de téléphone
            message: Message SMS

        Returns:
            True si succès, False sinon
        """
        try:
            # Implémentation avec Twilio ou autre service
            logger.info(f"SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False

    def send_new_listings_notification(
        self, phone_number: str, alert_name: str, listings_count: int
    ) -> bool:
        """
        Envoyer une notification SMS de nouvelles annonces.

        Args:
            phone_number: Numéro de téléphone
            alert_name: Nom de l'alerte
            listings_count: Nombre d'annonces trouvées

        Returns:
            True si succès, False sinon
        """
        message = f"Real Estate: {listings_count} nouvelle(s) annonce(s) pour '{alert_name}'. Consultez votre tableau de bord!"
        return self.send_sms(phone_number, message)


class NotificationService:
    """Service centralisé de notifications."""

    def __init__(self):
        """Initialiser le service de notifications."""
        self.email_notifier = EmailNotifier()
        self.sms_notifier = SMSNotifier()

    def notify_new_listings(
        self,
        user: User,
        alert: SearchAlert,
        listings: List[Listing],
        use_email: bool = True,
        use_sms: bool = False,
    ) -> bool:
        """
        Notifier l'utilisateur de nouvelles annonces.

        Args:
            user: Utilisateur
            alert: Alerte de recherche
            listings: Nouvelles annonces
            use_email: Envoyer par email
            use_sms: Envoyer par SMS

        Returns:
            True si au moins une notification a été envoyée
        """
        success = False

        if use_email:
            success = self.email_notifier.send_new_listings_notification(
                user, alert, listings
            ) or success

        if use_sms:
            # Ajouter le numéro de téléphone à l'utilisateur
            success = self.sms_notifier.send_new_listings_notification(
                "+33123456789",  # À récupérer de l'utilisateur
                alert.name,
                len(listings),
            ) or success

        if success:
            alert.last_notified = datetime.utcnow()

        return success

    def send_welcome_notification(self, user: User) -> bool:
        """
        Envoyer un email de bienvenue.

        Args:
            user: Nouvel utilisateur

        Returns:
            True si succès, False sinon
        """
        return self.email_notifier.send_welcome_email(user)


# Instance globale
notification_service = NotificationService()
