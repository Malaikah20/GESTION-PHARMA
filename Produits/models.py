from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
# Create your models here.
class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    # description = models.TextField()

    # def __str__(self):
    #     return self.nom
# la class meta est une classe interne qui permet de definir des options pour le modele, comme le nom de la table dans la base de donnees, le nom de l'objet dans l'admin, etc.
    class Meta:
        verbose_name = "categorie"
        verbose_name_plural = "categories"
# pour faire la surcharge de la methode str pour afficher le nom de la categorie dans l'admin on fait la methode str pour retourner le nom de la categorie
    def __str__(self):
        return self.nom



class Fournisseur(models.Model):
    nom = models.CharField("nom de l'entreprise ",max_length=100, unique=True)
    adresse_mail = models.EmailField("adresse_mail",max_length=200)
    contact = models.CharField("contact", max_length=20, blank=True)
    telephone = models.CharField("téléphone", max_length=20, blank=True)
    adresse = models.CharField("adresse", max_length=200, blank=True)
    note = models.TextField("note", blank=True)
    actif = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Client(models.Model):
    nom = models.CharField("nom du client", max_length=100, unique=True)
    prenom = models.CharField("prenom du client", max_length=100, blank=True)
    adresse_mail = models.EmailField("adresse_mail", max_length=200)
    contact = models.CharField("contact", max_length=20, blank=True)
    telephone = models.CharField("téléphone", max_length=20, blank=True)
    adresse = models.CharField("adresse", max_length=200, blank=True)
    note = models.TextField("note", blank=True, help_text = " allergies, maladies, etc.")
    actif = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ['nom', 'prenom']

    def __str__(self):
        nom_complet = f"{self.nom} {self.prenom}"
        return nom_complet or f"client {self.pk}".strip()  # Supprime les espaces inutiles si le prénom est vide

class Produit(models.Model):
    nom = models.CharField("nom du produit", max_length=100, unique=True)
    description = models.TextField("description", blank=True)
    prix_de_vente = models.DecimalField("prix de vente", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    prix_achat = models.DecimalField("prix d'achat", max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)], blank=True, null=True)
    quantite = models.PositiveIntegerField("quantité en stock", default=0, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField("stock", default=0, validators=[MinValueValidator(0)])
    seuil_alerte = models.PositiveIntegerField("seuil d'alerte", default=0, validators=[MinValueValidator(0)])
    numero_de_lot = models.CharField("numéro de lot", max_length=100, blank=True)
    date_de_peremption = models.DateField("date de péremption", null=True, blank=True)
    image = models.ImageField("image du produit", upload_to='produits/', null=True, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='produits')
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    actif = models.BooleanField("actif", default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom
    @property
    def en_rupture(self):
        return self.stock == 0
    @property
    def stock_faible(self):
        return 0 < self.stock <= self.seuil_alerte
    @property
    def peremption_proche(self):
        if not self.date_de_peremption:
            return False
        if self.date_de_peremption <= timezone.localdate() + timezone.timedelta(days=30):
            return True

class Vente(models.Model):

    class ModePaiement(models.TextChoices):
        ESPECE = 'ESP', 'Espèce'
        CARTE_BANCAIRE = 'CBK', 'Carte bancaire'
        mobile_money = 'MM', 'Mobile Money'

    class Statut(models.TextChoices):
        EN_COURS = 'ENC', 'En cours'
        TERMINEE = 'TERM', 'Terminée'
        ANNULEE = 'ANU', 'Annulée'

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventes', help_text= 'vide = client de passage')
    date = models.DateTimeField("date de la vente", auto_now_add=True)
    mode_de_paiement = models.CharField("mode de paiement", max_length=3, choices=ModePaiement.choices, default=ModePaiement.ESPECE)
    statut = models.CharField("statut de la vente", max_length=4, choices=Statut.choices, default=Statut.EN_COURS)
    remise = models.DecimalField("remise ", max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField("total de la vente", max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    note = models.TextField("note", blank=True)

    class Meta:
        ordering = ['-date']
    

    def __str__(self):
       return self.numero_facture  # Affiche le numéro de facture dans l'admin

    @property
    def numero_de_vente(self):
        return f"#{self.pk}"  # Format: V000001, V000002, etc.
    @property
    def numero_facture(self):
        annee = self.date.year if self.date else timezone.now().year
        return f"F{annee}-{self.pk}"  # Format:

    @property
    def status_css(self):
        return {
            self.Statut.EN_COURS: 'warning',
            self.Statut.TERMINEE: 'active',
            self.Statut.ANNULEE: 'danger',
        }.get(self.statut, 'info')

    @property
    def sous_total(self):
        return sum(ligne.total for ligne in self.lignes.all())

    @property
    def nb_articles(self):
        return sum(ligne.quantite for ligne in self.lignes.all()) 

class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='lignes_vente')
    quantite = models.PositiveIntegerField("quantité vendue", default=1, validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField("prix de vente du produit", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])


    def __str__(self):
        
        return f"{self.quantite} x {self.produit.nom} pour la vente {self.vente.pk}"
    
    @property
    def total (self):
        return self.quantite * self.prix_unitaire
    


















































# pour integrer le produit dans la vente, on cree un modele intermédiaire qui va contenir le produit, la vente et la quantité vendue. On peut aussi ajouter le prix de vente du produit au moment de la vente pour garder une trace du prix de vente à ce moment-là
# voici le code pour le modele intermédiaire:
# class vente_produit(models.Model):
#     vente = models.ForeignKey(vente, on_delete=models.CASCADE, related_name='produits')
#     produit = models.ForeignKey(produit, on_delete=models.PROTECT, related_name='ventes')
#     quantite = models.PositiveIntegerField("quantité vendue", default=1, validators=[MinValueValidator(1)])
#     prix_vente = models.DecimalField("prix de vente du produit", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

#     class Meta:
#         unique_together = ('vente', 'produit')  # Assure qu'un produit ne peut être ajouté qu'une seule fois à une vente

#     def __str__(self):
#         return f"{self.quantite} x {self.produit.nom} pour la vente {self.vente.id}"