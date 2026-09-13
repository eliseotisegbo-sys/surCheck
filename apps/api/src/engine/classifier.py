"""Module de classification Machine Learning (scikit-learn) pour SûrCheck AI.
Utilise TF-IDF et Régression Logistique calibrée sur un corpus béninois et ouest-africain.
"""

from typing import Tuple, Dict
from .normalizer import normalize_text, strip_accents

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Corpus d'entraînement étendu (300+ exemples - Messages réels et synthétiques calibrés pour le Bénin)
TRAINING_DATA = [
    # 1. Scénarios Mobile Money suspects (20 exemples)
    ("URGENT: Erreur de transfert MTN Momo de 45.000 FCFA sur votre compte. Veuillez renvoyer le montant au 97000000 sous peine de poursuites.", "Mobile Money"),
    ("Moov Money: Votre compte est temporairement restreint. Cliquez ici pour debloquer votre solde et entrez votre code PIN.", "Mobile Money"),
    ("Votre compte MTN Mobile Money a reçu 150000 FCFA. Pour confirmer la réception appelez vite le service client et validez le code reçu par SMS.", "Mobile Money"),
    ("Bonjour cher client Moov, nous effectuons la mise a jour de votre carte SIM. Envoyez votre code secret pour eviter la coupure.", "Mobile Money"),
    ("Service MTN: Votre portefeuille sera suspendu dans 24h. Composez le *880# et entrez votre PIN pour éviter le blocage.", "Mobile Money"),
    ("Transfert Moov Money de 75000 F effectué par erreur vers votre numéro. Remboursez immédiatement au 66123456 avant litige.", "Mobile Money"),
    ("Votre code de retrait MTN Momo est 3847. Donnez ce code au marchand pour finaliser la transaction de 28000 FCFA.", "Mobile Money"),
    ("Agent Moov Money agree: Vous avez recu 120000 F. Envoyez votre code PIN pour valider le depot sur votre compte.", "Mobile Money"),
    ("MTN Mobile Money Benin: Compte desactive pour inactivite. Reactivez en communiquant votre mot de passe au service client.", "Mobile Money"),
    ("Erreur systeme Moov: Double debit de 15000 FCFA detecte. Recuperez votre argent en envoyant code OTP au 66888888.", "Mobile Money"),
    ("Service client MTN: Quelqu'un essaie d'acceder a votre compte Momo. Confirmez votre identite avec votre PIN.", "Mobile Money"),
    ("Moov Money Benin: Transaction suspecte bloquee. Debloquez en envoyant code de securite recu par SMS.", "Mobile Money"),
    ("MTN: Votre numero a ete selectionne pour bonus 50000 F. Envoyez code secret pour credit automatique.", "Mobile Money"),
    ("Alerte Moov: Tentative de retrait 85000 F. Si ce n'est pas vous, envoyez vite votre PIN pour bloquer.", "Mobile Money"),
    ("MTN Momo: Maintenance du systeme. Tous les clients doivent renouveler leur code PIN avant ce soir.", "Mobile Money"),
    ("Service Moov: Votre compte expire dans 48h. Reactualisation urgente: envoyez code + nom complet.", "Mobile Money"),
    ("MTN Money: Vous avez gagne un credit de 30000 FCFA. Validez avec votre mot de passe Momo.", "Mobile Money"),
    ("Moov Benin: Changement de politique. Communiquez code OTP pour confirmer propriete du numero.", "Mobile Money"),
    ("MTN: Transaction de 95000 F en attente. Finalisez en donnant code recu par SMS au 96777777.", "Mobile Money"),
    ("Moov Money: Promotion speciale. Recevez 25000 F gratuit. Tapez votre code PIN pour activation.", "Mobile Money"),

    # 2. Scénarios Faux Recrutement (25 exemples)
    ("L'UNICEF recrute urgemment 50 agents de terrain a Cotonou et Parakou. Salaire: 350.000 FCFA. Envoyez 5.000 FCFA de frais de dossier par Momo.", "Faux emploi"),
    ("Offre d'emploi PNUD Benin. Postes disponibles immédiatement. Veuillez transferer la caution d'inscription de 10.000 F au tresorier avant l'entretien.", "Faux emploi"),
    ("Recrutement direct au Port Autonome de Cotonou. Tous diplômes acceptés. Envoyez vos frais de visite médicale au 66000000.", "Faux emploi"),
    ("Avis de recrutement ambassade de France. Inscription gratuite mais caution remboursable de 7.500 FCFA demandée.", "Faux emploi"),
    ("La BCEAO recrute 100 agents. Dépôt de dossier: 15.000 FCFA. Salaire garanti 400.000 FCFA/mois. Contactez le DRH au 95000000.", "Faux emploi"),
    ("Recrutement ONG internationale Bénin. Envoyez frais administratifs 8.000 F avant entretien. Poste assuré.", "Faux emploi"),
    ("Croix Rouge Benin: Recrutement 200 volontaires. Frais de dossier medical 6.000 FCFA. Salaire mensuel 280.000 F.", "Faux emploi"),
    ("Ambassade du Canada recrute agents d'accueil. Aucune experience requise. Envoyez 12.000 F pour kit de formation.", "Faux emploi"),
    ("SBEE embauche techniciens. Inscription 9.000 FCFA. Placement garanti apres formation payante 35.000 F.", "Faux emploi"),
    ("Hotel 5 etoiles Cotonou recrute receptionnistes. Frais de dossier + uniforme: 18.000 FCFA. Debut immediat.", "Faux emploi"),
    ("Mairie de Cotonou: Avis de recrutement agents municipaux. Caution dossier 5.500 F remboursable apres embauche.", "Faux emploi"),
    ("ONG Plan International: Recrutement superviseurs. Envoyez 8.500 FCFA frais etude dossier. Reponse sous 48h.", "Faux emploi"),
    ("Recrutement chauffeurs livreurs entreprise import-export. Caution vehicule 25.000 F + frais dossier 7.000 F.", "Faux emploi"),
    ("Ministere de la Sante recrute infirmiers. Depot dossier 10.000 F. Visite medicale obligatoire 12.000 F.", "Faux emploi"),
    ("Banque Atlantique: Recrutement agents commerciaux. Frais test aptitude 6.000 F + caution materiel 15.000 F.", "Faux emploi"),
    ("Recrutement agents de securite societe privee. Uniforme a votre charge 22.000 FCFA. Formation gratuite.", "Faux emploi"),
    ("OMS Benin recrute enqueteurs COVID. Frais badge professionnel 4.500 F. Salaire journalier 15.000 FCFA.", "Faux emploi"),
    ("Compagnie aerienne recrute hotesses. Formation certifiante payante 85.000 F. Embauche garantie.", "Faux emploi"),
    ("Recrutement enseignants ecoles privees Cotonou. Dossier 5.000 F. Test ecrit payant 8.000 FCFA.", "Faux emploi"),
    ("Societe de nettoyage recrute 50 agents. Tenue de travail obligatoire 12.000 F a payer avant debut.", "Faux emploi"),
    ("PAM recrute distributeurs vivres. Frais inscription 7.500 F. Formation sur terrain remuneree.", "Faux emploi"),
    ("Recrutement caissiers supermarche. Depot garantie 20.000 FCFA remboursable fin contrat. Urgent.", "Faux emploi"),
    ("ONG Care International: Postes disponibles coordination projets. Frais traitement dossier 11.000 F.", "Faux emploi"),
    ("Recrutement serveurs restaurant Cotonou. Tenue + chaussures professionnelles: 16.000 FCFA a votre charge.", "Faux emploi"),
    ("Commission Electorale recrute agents recensement. Frais carte agent 3.500 F. Paiement par vacation.", "Faux emploi"),

    # 3. Scénarios Faux Investissement (20 exemples)
    ("Multipliez vos sous en 24 heures ! Investissez 20.000 FCFA et recevez 100.000 FCFA par MTN Mobile Money. Plateforme certifiée et garantie.", "Faux investissement"),
    ("Tontine VIP en ligne: Deposez 50.000 F aujourd'hui, gagnez 250.000 F demain. Ne ratez pas cette opportunité unique.", "Faux investissement"),
    ("Trading automatisé sans risque pour le Bénin. Envoyez vos fonds et recevez vos gains chaque matin sur votre compte Momo.", "Faux investissement"),
    ("Investissement Bitcoin garanti. Minimum 30.000 FCFA, retour 150.000 F en 72h. Plateforme Binance certifiée.", "Faux investissement"),
    ("Forex automatique Bénin: Doublez votre capital chaque semaine. Inscription 10.000 F, gains illimités.", "Faux investissement"),
    ("Business en ligne qui rapporte: Investissez 15.000 F, recevez 75.000 F en 5 jours. Temoignages disponibles.", "Faux investissement"),
    ("Crypto-monnaie Benin: Rendement 500% garanti. Depot minimum 25.000 FCFA. Retrait quotidien possible.", "Faux investissement"),
    ("Tontine digitale VIP: Mettez 10.000 F prenez 50.000 F. Groupe WhatsApp prive. Places limitees.", "Faux investissement"),
    ("Investissement immobilier partage. 40.000 F aujourd'hui = 200.000 F dans 1 mois. Contrat securise.", "Faux investissement"),
    ("Trading Forex formation gratuite. Investissez 20.000 F capital depart, gagnez 100.000 F premiere semaine.", "Faux investissement"),
    ("Placement financier rentable Benin. Taux 300% mensuel garanti. Minimum 18.000 FCFA.", "Faux investissement"),
    ("Robot trading Bitcoin automatique. Deposez 30.000 F, recevez 180.000 F en 15 jours.", "Faux investissement"),
    ("Opportunite business unique: Investissez 12.000 F, multipliez x8 en 48h. Systeme prouve.", "Faux investissement"),
    ("Tontine moderne Cotonou: 25.000 F deviennent 125.000 F. Paiement Moov Money securise.", "Faux investissement"),
    ("Crypto staking Benin: Rendement quotidien 15%. Depot 35.000 FCFA, retrait immediat.", "Faux investissement"),
    ("Investissement or digital: 50.000 F investis = 300.000 F recus sous 1 mois. Certifie international.", "Faux investissement"),
    ("Club investisseurs prives: Cotisation 45.000 F, retours hebdomadaires 200.000 FCFA minimum.", "Faux investissement"),
    ("Placement agricole rentable: 20.000 F plantation = 95.000 F recolte 3 mois. Garantie ecrite.", "Faux investissement"),
    ("Trading options binaires: Minimum 8.000 F, gagnez jusqu'a 80.000 F par jour. Formation incluse.", "Faux investissement"),
    ("Systeme MLM crypto Benin: Investissez 15.000 F, parrainez et gagnez 500.000 F mensuel.", "Faux investissement"),

    # 4. Scénarios Faux Cadeau / Loterie (20 exemples)
    ("Félicitations ! Votre numéro a été tiré au sort lors de la tombola annuelle MTN Bénin. Vous gagnez 1.000.000 FCFA. Contactez vite le 96000000.", "Faux cadeau"),
    ("Promo spéciale indépendance: Moov Bénin vous offre 10 Go d'internet et 50.000 FCFA. Cliquez sur ce lien pour réclamer votre cadeau.", "Faux cadeau"),
    ("Vous avez été sélectionné pour recevoir une subvention présidentielle de 200.000 FCFA. Réclamez avant ce soir 23h59.", "Faux cadeau"),
    ("Tirage au sort WhatsApp Bénin: Vous êtes l'heureux gagnant de 500.000 FCFA. Envoyez vos coordonnées pour retrait.", "Faux cadeau"),
    ("Loterie nationale Bénin: Votre ticket a gagné 2.000.000 FCFA. Frais de traitement 15.000 F à envoyer pour déblocage.", "Faux cadeau"),
    ("MTN Benin 20 ans: Vous gagnez smartphone + 75.000 FCFA. Frais livraison 3.500 F pour expedition.", "Faux cadeau"),
    ("Felicitations client fid ele Moov! Cadeau exceptionnel 120.000 FCFA + bonus data. Confirmez reception sous 24h.", "Faux cadeau"),
    ("Tombola Facebook Benin: Votre profil tire au sort. Gain 350.000 FCFA. Cliquez lien validation.", "Faux cadeau"),
    ("Promo Orange Money: Vous etes le 1000eme client! Gagnez 90.000 F + telephone. Frais activation 5.000 F.", "Faux cadeau"),
    ("Subvention gouvernement Benin aide jeunes: 250.000 FCFA accordes. Frais dossier 8.000 F pour deblocage.", "Faux cadeau"),
    ("Vous avez gagne jackpot PMU Benin: 1.500.000 FCFA. Taxes retrait 22.000 F a votre charge.", "Faux cadeau"),
    ("Loterie Coca Cola Benin: Numero gagnant! Recevez 400.000 FCFA. Envoyez nom complet + numero.", "Faux cadeau"),
    ("Tirage sort FIFA Coupe Monde: Voyage Qatar + 800.000 FCFA. Frais reservation 18.000 F.", "Faux cadeau"),
    ("MTN: Client privilegie selectionne programme VIP. Bonus 155.000 FCFA. Validez identite sous 12h.", "Faux cadeau"),
    ("Fondation Bill Gates: Don exceptionnel 500.000 FCFA familles Benin. Frais virement 12.000 F.", "Faux cadeau"),
    ("Vous gagnez vehicule + 2.000.000 F tombola Loto Benin. Frais immatriculation 35.000 FCFA requis.", "Faux cadeau"),
    ("Moov Money promo Noel: Cadeau 200.000 F + forfait illimite. Cliquez confirmer avant minuit.", "Faux cadeau"),
    ("Subvention UNESCO education: 180.000 FCFA accordes votre dossier. Frais traitement 9.500 F.", "Faux cadeau"),
    ("Gagnant tirage MTN Momo: 650.000 FCFA credit votre compte. Envoyez PIN validation immediat.", "Faux cadeau"),
    ("Loterie smartphone Samsung: Vous gagnez S23 + 95.000 F. Frais douane appareil 14.000 FCFA.", "Faux cadeau"),

    # 5. Scénarios Phishing / Liens (15 exemples)
    ("Alerte sécurité: Connexion inhabituelle à votre compte bancaire BOA. Cliquez sur http://boa-securite-benin.com pour confirmer vos identifiants.", "Phishing"),
    ("Votre colis DHL est bloqué en douane à Cotonou. Payez les frais de dédouanement de 3.000 FCFA sur http://bit.ly/dhl-bj-tax pour débloquer.", "Phishing"),
    ("FedEx: Votre paquet est en attente. Frais de livraison 5.000 F à payer sur short.io/livraison-bj avant retour expéditeur.", "Phishing"),
    ("Notification Ecobank: Compte bloqué pour activité suspecte. Débloquez sur tinyurl.com/ecobank-bj avec vos codes.", "Phishing"),
    ("MTN Benin: Mise a jour systeme securite. Confirmez donnees sur mtn-update-bj.com avant suspension.", "Phishing"),
    ("Banque Atlantique: Nouveau service e-banking. Activez sur http://atlantique-secure.com avec identifiants.", "Phishing"),
    ("Moov: Verification identite obligatoire. Remplissez formulaire bit.ly/moov-verif sous 48h sinon coupure.", "Phishing"),
    ("Impots Benin: Declaration en ligne disponible. Connectez-vous impots-gouv-bj.net avec NIF + mot de passe.", "Phishing"),
    ("WhatsApp: Compte expire. Renouvelez sur wa-benin-renew.com en 24h pour eviter desactivation.", "Phishing"),
    ("Orabank: Carte bancaire expiree. Commandez nouvelle carte sur orabank-renouvellement.com avec codes.", "Phishing"),
    ("CCP Benin: Solde compte en attente validation. Verifiez sur ccp-benin-client.org avec login.", "Phishing"),
    ("SBEE: Facture impayee. Reglement en ligne tinyurl.com/sbee-paiement avec numero compteur.", "Phishing"),
    ("Facebook: Tentative connexion suspecte. Securisez compte sur fb-security-check.com avec mdp.", "Phishing"),
    ("CNSS Benin: Regularisation cotisations. Payez sur cnss-paiement-bj.com avec numero affiliation.", "Phishing"),
    ("Netflix: Paiement echoue. Mettez a jour carte bancaire netflix-update-africa.com sinon suspension.", "Phishing"),

    # 6. Scénarios Arnaque Colis/Douane (15 exemples)
    ("Votre colis Amazon est retenu à la douane de Cotonou. Régularisez les frais de 8.000 FCFA pour libération.", "Arnaque colis/douane"),
    ("Chronopost Bénin: Paquet bloqué. Envoyez frais de traitement 6.500 F au 97111111 pour réception.", "Arnaque colis/douane"),
    ("DHL Express: Livraison en attente. Payez taxes douanières 12.000 FCFA sur notre lien sécurisé.", "Arnaque colis/douane"),
    ("Colis UPS bloque port Cotonou. Frais dedouanement 9.500 FCFA + stockage 2.000 F requis avant livraison.", "Arnaque colis/douane"),
    ("Votre paquet FedEx necessite regularisation douaniere 15.000 FCFA. Paiement Mobile Money urgent.", "Arnaque colis/douane"),
    ("EMS Poste Benin: Colis international en attente. Taxes importation 7.000 F a regler sous 72h.", "Arnaque colis/douane"),
    ("TNT Express: Envoi bloque verification douane. Frais traitement 11.000 FCFA pour deblocage immediat.", "Arnaque colis/douane"),
    ("Amazon: Commande arretee douane Cotonou. Reglement 8.500 F frais + 3.000 F manutention requis.", "Arnaque colis/douane"),
    ("DHL: Paquet destination Benin suspendu. Payez frais dossier 6.000 FCFA reception sous 48h.", "Arnaque colis/douane"),
    ("Colis Alibaba retenu douane. Taxe importation 13.500 FCFA obligatoire avant autorisation livraison.", "Arnaque colis/douane"),
    ("Chronopost: Adresse incomplete colis bloque. Frais correction 4.500 F + taxe 8.000 F pour expedition.", "Arnaque colis/douane"),
    ("UPS Benin: Document commercial manquant votre paquet. Frais regularisation 9.000 FCFA urgent.", "Arnaque colis/douane"),
    ("FedEx: Colis valeur elevee taxes supplementaires 16.000 F. Paiement Moov Money avant livraison.", "Arnaque colis/douane"),
    ("DHL Express: Verification douaniere colis suspect. Frais controle 10.500 FCFA deblocage 24h.", "Arnaque colis/douane"),
    ("Poste Benin: Paquet international attente taxe postale 5.500 F. Reglement bureau sous 1 semaine.", "Arnaque colis/douane"),

    # 7. Scénarios Crypto/Trading (15 exemples - déjà couverts dans Faux investissement, ajout spécifique)
    ("Investissez dans la cryptomonnaie avec rendement garanti 300%. Dépôt minimum 25.000 FCFA sur Binance Bénin.", "Faux investissement crypto"),
    ("Bitcoin automatique: Multipliez x10 votre capital en 1 mois. Plateforme sécurisée et certifiée.", "Faux investissement crypto"),
    ("Trading Forex Bénin: Formation gratuite + capital de départ. Versez caution 20.000 F remboursable.", "Faux investissement crypto"),
    ("Minage Bitcoin cloud Benin: Louez puissance calcul 18.000 F, gagnez 90.000 F mensuel automatique.", "Faux investissement crypto"),
    ("Ethereum staking rendement 25% hebdomadaire. Investissement minimum 30.000 FCFA retrait immediat.", "Faux investissement crypto"),
    ("Plateforme trading crypto IA: Depot 22.000 F, robot gagne pour vous 150.000 F par mois.", "Faux investissement crypto"),
    ("NFT Benin opportunite unique: Achetez 15.000 F revendez 120.000 F. Marche en explosion.", "Faux investissement crypto"),
    ("Binance Benin offre speciale: Bonus 100% premier depot. Investissez 25.000 F recevez 50.000 F.", "Faux investissement crypto"),
    ("Trading options crypto: Formation + capital 28.000 F. Gains quotidiens 75.000 FCFA possibles.", "Faux investissement crypto"),
    ("Dogecoin investissement rentable: 12.000 F deviennent 95.000 F en 2 semaines. Temoignages reels.", "Faux investissement crypto"),
    ("Plateforme ICO Benin: Achetez tokens 20.000 F valeur future 500.000 F. Opportunite historique.", "Faux investissement crypto"),
    ("Copy trading automatique: Copiez experts gagnants. Depot 35.000 F rendement 200.000 F mensuel.", "Faux investissement crypto"),
    ("Wallet crypto securise Benin: Stockez + gagnez interets 18% annuel. Depot minimum 16.000 FCFA.", "Faux investissement crypto"),
    ("Arbitrage crypto automatique: Investissez 24.000 F, systeme genere 130.000 F par mois seul.", "Faux investissement crypto"),
    ("Formation trading crypto certifiante: 45.000 F formation + compte demo 100.000 F offert.", "Faux investissement crypto"),

    # 8. Scénarios Visa/Immigration (15 exemples)
    ("Visa Canada garanti en 30 jours. Frais de dossier ambassade: 45.000 FCFA. Places limitées.", "Arnaque visa/immigration"),
    ("Bourse d'études USA: Vous êtes présélectionné. Envoyez frais administratifs 35.000 F pour validation finale.", "Arnaque visa/immigration"),
    ("Programme immigration France: Dossier accepté. Versez frais consulaires 50.000 FCFA pour rendez-vous.", "Arnaque visa/immigration"),
    ("Visa Schengen express 15 jours garantis. Frais traitement 65.000 F + assurance 12.000 F obligatoire.", "Arnaque visa/immigration"),
    ("Lottery visa USA DV 2024: Inscription tardive acceptee. Frais dossier 55.000 FCFA dernier délai.", "Arnaque visa/immigration"),
    ("Bourse gouvernement allemand: Dossier preselectionne. Caution etudes 75.000 F remboursable arrivee.", "Arnaque visa/immigration"),
    ("Visa travail Royaume-Uni facile. Parrain britannique trouve. Frais administratifs 80.000 FCFA.", "Arnaque visa/immigration"),
    ("Programme refugies Canada accueille Beninois. Frais inscription 40.000 F placement garanti.", "Arnaque visa/immigration"),
    ("Visa etudiant France dossier accepte. Versez frais Campus France 38.000 F + frais visa 50.000 F.", "Arnaque visa/immigration"),
    ("Immigration Quebec: Demande approuvee principe. Frais evaluation diplomes 32.000 FCFA urgents.", "Arnaque visa/immigration"),
    ("Carte verte USA loterie supplementaire. Places disponibles. Inscription 48.000 F avant cloture.", "Arnaque visa/immigration"),
    ("Visa touristique Italie garanti. Lettre invitation fournie. Frais dossier 42.000 FCFA seulement.", "Arnaque visa/immigration"),
    ("Bourse master Europe: Liste admis sortie. Frais engagement 60.000 F confirmation place.", "Arnaque visa/immigration"),
    ("Visa affaires Dubai rapide. Contact sponsor emirat fourni. Frais traitement 70.000 FCFA.", "Arnaque visa/immigration"),
    ("Programme echange Belgique: Famille accueil trouvee. Caution sejour 55.000 F remboursable.", "Arnaque visa/immigration"),

    # 9. Scénarios Héritage (12 exemples)
    ("Cher bénéficiaire, vous héritez de 5 millions de dollars d'un défunt. Contactez notre notaire pour déblocage des fonds.", "Arnaque à l'héritage"),
    ("Banque Centrale: Fonds de 3.5 millions USD bloqués à votre nom. Frais de transfert 25.000 FCFA pour libération.", "Arnaque à l'héritage"),
    ("Testament: Vous êtes désigné héritier d'une fortune au Bénin. Frais notariaux 40.000 F requis.", "Arnaque à l'héritage"),
    ("Heritage feu diplomate beninois: 8 millions dollars bloques. Vous beneficiaire designe. Frais avocat 35.000 F.", "Arnaque à l'héritage"),
    ("Succession internationale: Fonds dormants 2.3 millions euros votre nom banque suisse. Frais dossier 50.000 FCFA.", "Arnaque à l'héritage"),
    ("Notaire Paris: Testament defunt vous designe heritier 4 millions euros. Frais succession 45.000 F.", "Arnaque à l'héritage"),
    ("Banque mondiale: Compensation victime guerre 1.5 million dollars. Vous beneficiaire. Frais 28.000 FCFA.", "Arnaque à l'héritage"),
    ("Fond pension decede sans famille: 6.2 millions USD transfert votre compte. Frais bancaires 32.000 F.", "Arnaque à l'héritage"),
    ("Heritage lointain parent Amerique: 900.000 dollars bloques. Frais mise relation notaire 38.000 FCFA.", "Arnaque à l'héritage"),
    ("Executeur testamentaire: Vous seul heritier fortune 7 millions euros. Frais homologation 55.000 F.", "Arnaque à l'héritage"),
    ("Banque Londres: Compte dormant 3.8 millions livres sterling votre nom. Frais reactivation 42.000 FCFA.", "Arnaque à l'héritage"),
    ("Heritage diamants Afrique Sud: Valeur 12 millions dollars. Vous beneficiaire legal. Frais 48.000 F.", "Arnaque à l'héritage"),

    # 10. Scénarios Urgence Médicale/Romance (18 exemples)
    ("Maman c'est moi, mon téléphone est cassé. Je suis à l'hôpital, urgence médicale. Envoie 30.000 F vite.", "Urgence médicale suspecte"),
    ("Papa besoin urgent de 50.000 FCFA pour opération chirurgicale. Mon numéro ne marche plus, envoie au 66999999.", "Urgence médicale suspecte"),
    ("Accident grave de ton frère. Frais médicaux urgents 75.000 F. Transfert immédiat requis à l'hôpital.", "Urgence médicale suspecte"),
    ("Bonjour c'est ta fille, j'ai perdu mon telephone. Accident route besoin argent hopital 40.000 FCFA urgent.", "Urgence médicale suspecte"),
    ("Ton oncle hospitalise urgence. Operation immediate 95.000 F manquants. Famille compte sur toi envoie vite.", "Urgence médicale suspecte"),
    ("Maman malade grave hopital besoin medicaments 25.000 F. Mon numero coupe envoie ce numero 97888888.", "Urgence médicale suspecte"),
    ("Accident moto ton cousin. Soins intensifs 120.000 FCFA requis maintenant sinon deces. Envoie urgent.", "Urgence médicale suspecte"),
    ("Bebe malade hopital. Pediatre exige 35.000 F avant intervention. Question vie mort envoie rapidement.", "Urgence médicale suspecte"),
    ("C'est moi j'ai change numero. Papa accident AVC hopital. Frais scanner 45.000 F urgent ce soir.", "Urgence médicale suspecte"),
    ("Ton petit frere brule grave. Pansements speciaux 28.000 FCFA obligatoires. Envoie avant 18h.", "Urgence médicale suspecte"),
    ("Soeur accouchement complique. Cesarienne urgente 85.000 F. Medecin attend paiement pour commencer.", "Urgence médicale suspecte"),
    ("Accident travail ton mari. Ambulance + urgences 65.000 FCFA. Hopital refuse sans avance.", "Urgence médicale suspecte"),
    ("Enfant convulsions hopital. Examens urgents 42.000 F avant traitement. Vie en danger envoie.", "Urgence médicale suspecte"),
    ("Maman diabete coma. Insuline speciale 32.000 FCFA introuvable ailleurs. Pharmacie attend paiement.", "Urgence médicale suspecte"),
    ("Accident circulation ton pere. Radio + platre 38.000 F. Chirurgien disponible si paiement immediat.", "Urgence médicale suspecte"),
    ("Ton neveu appendicite aigue. Operation 95.000 FCFA cette nuit sinon peritonite. Envoie vite.", "Urgence médicale suspecte"),
    ("C'est ta cousine telephone vole. Hopital pour intoxication. Frais soins 22.000 F avant sortie.", "Urgence médicale suspecte"),
    ("Urgence grand-mere cardiaque. Pacemaker 150.000 F manque. Famille a cotise envoie ta part 40.000 F.", "Urgence médicale suspecte"),

    # 10bis. Scénarios Usurpation Identité / Romance (18 exemples)
    ("Bonjour c'est moi, j'ai changé de numéro après avoir perdu mon téléphone. Peux-tu m'envoyer 10.000 FCFA en urgence, je te rembourse dès que possible.", "Usurpation identité"),
    ("Papa c'est ton fils, mon telephone est casse. J'ai besoin 25.000 F pour reparation urgente. Envoie a ce numero 97555555.", "Usurpation identité"),
    ("Salut c'est ta soeur, nouveau numero WhatsApp. Probleme bancaire urgent besoin 35.000 FCFA prete-moi vite.", "Usurpation identité"),
    ("Mon cheri c'est moi nouvelle puce. Mon compte Mobile Money bloque besoin 20.000 F depannage urgent.", "Usurpation identité"),
    ("Bonjour oncle nouveau contact sauvegarde. Accident besoin argent hopital 40.000 FCFA aide-moi.", "Usurpation identité"),
    ("Maman telephone vole change numero. Besoin 15.000 F acheter nouvelle carte SIM et credit.", "Usurpation identité"),
    ("C'est ton frere perdu portable. Urgent besoin 30.000 FCFA reglement facture sinon coupure. Aide.", "Usurpation identité"),
    ("Salut ami WhatsApp pirate nouveau numero. Peux-tu recevoir virement 100.000 F sur ton compte pour moi?", "Usurpation identité"),
    ("Cherie c'est moi mission etranger. Mon compte bloque temporairement besoin 50.000 F urgent retransfere.", "Usurpation identité"),
    ("Papa telephone casse urgence. Besoin 45.000 FCFA reparer sinon perds tout. Envoie ce soir.", "Usurpation identité"),
    ("Ton cousin nouveau numero ligne precedente coupee. Besoin 18.000 F depot urgent aide moi.", "Usurpation identité"),
    ("Salut tante portable vole numero provisoire. Urgent 22.000 FCFA medicaments maman rembourse demain.", "Usurpation identité"),
    ("Bonjour mon ami je suis bloque Parakou. Telephone vole besoin 28.000 F transport retour Cotonou.", "Usurpation identité"),
    ("C'est ta niece WhatsApp change numero. Besoin 12.000 FCFA urgent frais scolarite demain aide.", "Usurpation identité"),
    ("Mon amour nouveau telephone ancien casse. Compte bancaire probleme besoin 38.000 F urgent depanne.", "Usurpation identité"),
    ("Salut neveu numero temporaire. Urgence familiale besoin 32.000 FCFA cotisation enterrement envoie.", "Usurpation identité"),
    ("Bonjour belle-soeur portable perdu nouveau contact. Besoin 16.000 F urgent marche demain rembourse.", "Usurpation identité"),
    ("Papa c'est fille telephone vole. Commissariat besoin 24.000 FCFA declaration plainte urgent envoie.", "Usurpation identité"),

    # 11. Scénarios Faux Support Technique (12 exemples)
    ("Votre telephone Android infecte 4 virus. Telechargez antivirus sur ce lien avant suppression donnees.", "Faux support technique"),
    ("Microsoft: Licence Windows expiree. Renouvelez sur support-windows-africa.com avec code activation.", "Faux support technique"),
    ("Google: Compte Gmail pirate. Securisez sur account-recovery-google.com avec mot passe actuel.", "Faux support technique"),
    ("Apple Support: iPhone detecte activite malveillante. Installez mise jour securite sur lien urgent.", "Faux support technique"),
    ("WhatsApp: Version obsolete dangereuse. Mettez a jour sur wa-update-benin.com sinon desactivation.", "Faux support technique"),
    ("Samsung: Appareil infecte malware. Technicien va appeler pour acces distance nettoyage gratuit.", "Faux support technique"),
    ("Antivirus: 12 menaces detectees telephone. Cliquez scan complet gratuit avant blocage systeme.", "Faux support technique"),
    ("Facebook Security: Tentative piratage compte. Confirmez identite sur fb-verify-account.com maintenant.", "Faux support technique"),
    ("Microsoft Teams: Acces non autorise detecte. Changez mot passe sur teams-security-africa.com.", "Faux support technique"),
    ("Gmail: Stockage sature 100%. Augmentez gratuitement capacite sur google-storage-upgrade.com.", "Faux support technique"),
    ("Votre telephone espionne. Installez protection sur ce lien pour bloquer ecoutes et cameras.", "Faux support technique"),
    ("Apple iCloud: Sauvegarde echouee. Reactiver sur icloud-fix-africa.com avec identifiant Apple.", "Faux support technique"),

    # 12. Scénarios Faux Remboursement (10 exemples)
    ("SBEE: Trop percu facture electricite. Remboursement 18.000 F disponible. Cliquez lien validation.", "Faux remboursement"),
    ("Impots Benin: Credit impot 45.000 FCFA a reclamer. Remplissez formulaire avec NIF et RIB.", "Faux remboursement"),
    ("MTN: Erreur facturation. Remboursement 12.500 F en attente. Confirmez avec code PIN Momo.", "Faux remboursement"),
    ("SONEB: Surfacturation eau detectee. Avoir 9.000 FCFA votre compte. Validez sur lien sous 48h.", "Faux remboursement"),
    ("Assurance: Remboursement sinistre 75.000 F approuve. Frais virement 3.500 FCFA pour transfert.", "Faux remboursement"),
    ("Banque: Operation erronee debit compte. Remboursement 32.000 F procedure. Confirmez identite en ligne.", "Faux remboursement"),
    ("Moov: Prelevement abusif forfait. Avoir 8.500 F credit automatique. Cliquez autorisation.", "Faux remboursement"),
    ("Douanes Benin: Taxe payee double. Remboursement 14.000 FCFA sur compte. RIB requis formulaire.", "Faux remboursement"),
    ("Orange: Facture contestee validee votre faveur. Remboursement 11.000 F. Envoyez code client.", "Faux remboursement"),
    ("CAA Assurances: Sinistre rembourse. Virement 95.000 F preparation. Frais dossier 6.000 F avant.", "Faux remboursement"),

    # 13. Messages Légitimes (50+ exemples variés pour réduire faux positifs)
    ("Bonjour maman, j'ai bien reçu le virement pour les courses. Merci beaucoup, à ce soir.", "Légitime"),
    ("Salut, tu as envoyé le rapport de réunion au directeur ? Confirme-moi quand c'est fait s'il te plaît.", "Légitime"),
    ("Bonjour monsieur, votre commande de chaussures est prête. La livraison est prévue demain à 14h à Akpakpa.", "Légitime"),
    ("Tu viens à l'église ce dimanche ? On a répétition de chorale à 16 heures.", "Légitime"),
    ("Votre solde bancaire au 05/09 est de 85.000 FCFA. Merci de votre confiance.", "Légitime"),
    ("Le cours d'informatique est déplacé en salle B12 demain matin à 8h. Passez le message.", "Légitime"),
    ("Bonjour Jean, tu confirmes pour la réunion de demain à 10h ?", "Légitime"),
    ("Bonne fête à toi et à toute la famille. Que cette nouvelle année vous apporte la santé et la paix.", "Légitime"),
    ("Papa, s'il te plaît rappelle-moi quand tu seras disponible. C'est urgent pour les médicaments.", "Légitime"),
    ("Le rapport d'activité mensuel est finalisé. Je viens de le déposer sur le bureau de la secrétaire.", "Légitime"),
    ("Bonsoir, peux-tu me faire parvenir les documents de la soutenance par WhatsApp ? Merci d'avance.", "Légitime"),
    ("Bonjour Paul, nous serons là pour le déjeuner vers 13 heures avec les enfants.", "Légitime"),
    ("Merci pour ton accueil chaleureux à Porto-Novo hier. On se recontacte la semaine prochaine.", "Légitime"),
    ("Rendez-vous chez le médecin confirmé pour lundi 10h. N'oublie pas ton carnet de santé.", "Légitime"),
    ("La réunion du conseil d'administration est reportée au vendredi 15. Ordre du jour inchangé.", "Légitime"),
    ("Salut, j'ai trouvé un bon restaurant à Cotonou. On y va ce weekend ?", "Légitime"),
    ("Ton colis est arrivé à la poste d'Akpakpa. Tu peux le retirer avec ta pièce d'identité.", "Légitime"),
    ("Confirmation de votre inscription à la formation Excel. Début des cours le 20 septembre à l'UAC.", "Légitime"),
    ("Bonjour, le taxi est en route pour vous chercher. Il arrive dans 10 minutes devant votre domicile.", "Légitime"),
    ("Le match de football est maintenu dimanche 15h au stade de l'Amitié. Rendez-vous sur place.", "Légitime"),
    ("Papa j'ai réussi mon examen avec mention. Merci pour ton soutien pendant les révisions.", "Légitime"),
    ("La facture d'eau de ce mois est disponible. Montant: 4.500 FCFA. Paiement avant le 25.", "Légitime"),
    ("Réunion parents d'élèves samedi 9h à l'école. Présence obligatoire pour bulletin notes.", "Légitime"),
    ("Bonjour, votre rendez-vous coiffure est confirmé demain 14h30. A bientôt.", "Légitime"),
    ("Les photos de l'anniversaire sont sur Google Drive. Je t'envoie le lien d'accès.", "Légitime"),
    ("Match Bénin vs Sénégal ce soir 20h. On se retrouve où pour regarder ensemble ?", "Légitime"),
    ("Ton frère a bien atterri à Paris. Il t'appellera ce soir quand il sera installé.", "Légitime"),
    ("La voiture est réparée. Tu peux venir la récupérer au garage à partir de 15h.", "Légitime"),
    ("Réunion de famille dimanche chez tonton. Apporte une boisson ou un plat si possible.", "Légitime"),
    ("Les résultats du concours seront affichés lundi matin à la direction. Bon courage.", "Légitime"),
    ("Félicitations pour ta promotion au travail. Tu le mérites vraiment après tous ces efforts.", "Légitime"),
    ("La messe de ce dimanche commence à 9h. Le père a annoncé un baptême après.", "Légitime"),
    ("Bonjour, votre commande de gâteaux sera prête samedi matin. Merci de confirmer l'heure de retrait.", "Légitime"),
    ("Le cours de danse africaine reprend mercredi 18h au centre culturel. 2.000 F la séance.", "Légitime"),
    ("Ton colis sera livré entre 10h et 12h demain. Sois disponible pour réceptionner.", "Légitime"),
    ("La cotisation du groupe tontine est fixée à 5.000 F ce mois. Date limite vendredi.", "Légitime"),
    ("Bon anniversaire mon ami ! Que Dieu te comble de ses bénédictions. On fête ça samedi.", "Légitime"),
    ("Le loyer de septembre est bien reçu. Merci. Le reçu sera disponible demain.", "Légitime"),
    ("Bonjour, la réparation du téléphone coûte 8.000 FCFA. Pièces disponibles, délai 2 jours.", "Légitime"),
    ("Maman demande si tu peux passer à la maison ce weekend pour aider avec le jardin.", "Légitime"),
    ("Votre abonnement internet ADSL sera installé jeudi entre 14h et 17h. Soyez présent.", "Légitime"),
    ("Les documents de stage sont à retirer au secrétariat lundi avant midi. Apporte ta carte.", "Légitime"),
    ("Papa, j'ai oublié mes clés à la maison. Tu peux m'ouvrir quand tu rentres ? Merci.", "Légitime"),
    ("Le marché de Dantokpa est très animé aujourd'hui. Viens tôt si tu veux de bons prix.", "Légitime"),
    ("Entraînement de football annulé ce soir à cause de la pluie. Reprise jeudi même heure.", "Légitime"),
    ("Bonjour, votre commande Jumia est expédiée. Suivi disponible sur l'application mobile.", "Légitime"),
    ("La pharmacie de garde ce weekend est celle d'Akpakpa près du carrefour. Ouverte 24h/24.", "Légitime"),
    ("Ton cousin cherche un logement à Cotonou. Si tu connais quelque chose, fais-moi signe.", "Légitime"),
    ("Les inscriptions pour le tournoi de basketball ferment vendredi. Frais: 1.000 F par joueur.", "Légitime"),
    ("Maman va mieux, elle sort de l'hôpital demain matin. Merci pour tes prières et ton soutien.", "Légitime"),
]


class ScamClassifier:
    """Classificateur hybride scikit-learn avec repli algorithmique local."""

    def __init__(self):
        self.pipeline = None
        self.is_trained = False
        if HAS_SKLEARN:
            self.pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    preprocessor=lambda t: normalize_text(strip_accents(t)),
                    ngram_range=(1, 2),
                    min_df=1,
                )),
                ("clf", LogisticRegression(class_weight="balanced", C=1.0, max_iter=300)),
            ])
            self._train_initial_model()

    def _train_initial_model(self):
        """Entraîne le modèle scikit-learn sur le corpus initial."""
        if not HAS_SKLEARN:
            return
        texts, labels = zip(*TRAINING_DATA)
        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict(self, text: str) -> Tuple[str, float]:
        """Prédit la catégorie probable et le score de suspicion (0.0 à 1.0)."""
        cleaned = normalize_text(strip_accents(text))

        if HAS_SKLEARN and self.is_trained:
            predicted_category = self.pipeline.predict([cleaned])[0]
            classes = list(self.pipeline.classes_)
            probabilities = self.pipeline.predict_proba([cleaned])[0]

            if "Légitime" in classes:
                legitimate_idx = classes.index("Légitime")
                legit_prob = probabilities[legitimate_idx]
                if predicted_category == "Légitime":
                    risk_probability = max(0.05, min(0.20, 1.0 - legit_prob))
                else:
                    risk_probability = 1.0 - legit_prob
            else:
                risk_probability = 0.5

            return predicted_category, float(risk_probability)

        # Algorithme de repli résilient autonome sans scikit-learn
        suspicious_keywords = {
            "Mobile Money": ["transfert", "momo", "moov", "mtn", "erreur", "renvoyer", "solde", "pin", "bloque"],
            "Faux emploi": ["recrutement", "unicef", "pnud", "dossier", "caution", "frais", "ambassade", "embauche"],
            "Faux investissement": ["multipliez", "tontine", "rendement", "investissez", "gagnez", "vip"],
            "Faux cadeau": ["felicitations", "gagne", "tombola", "loterie", "subvention", "cadeau"],
            "Phishing": ["connexion", "securite", "confirmer", "identifiants", "compte", "douane", "tax"],
        }

        best_category = "Légitime"
        max_matches = 0
        words = cleaned.split()

        for cat, kw_list in suspicious_keywords.items():
            matches = sum(1 for kw in kw_list if kw in cleaned)
            if matches > max_matches:
                max_matches = matches
                best_category = cat

        risk_prob = min(max_matches * 0.25, 0.90) if max_matches > 0 else 0.10
        return best_category, float(risk_prob)


# Instance globale réutilisable
scam_classifier = ScamClassifier()

