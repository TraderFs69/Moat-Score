🏰 Moat Scanner – S&P 500
Analyse de l’avantage concurrentiel (Moat) – approche relative sectorielle

Ce projet vise à évaluer la solidité de l’avantage concurrentiel (economic moat) des entreprises du S&P 500, à partir de données financières publiques (Yahoo Finance), selon une approche long terme et relative par secteur.

Contrairement à un score absolu, le Moat Score ici est comparatif :

une entreprise est jugée par rapport à ses pairs du même secteur.

📊 Description des colonnes du fichier CSV
🔹 Ticker

Symbole boursier de l’entreprise (ex. MSFT, AAPL, JNJ)

Sert d’identifiant unique

🔹 Sector

Secteur économique (selon Yahoo Finance)

Exemples :

Technology

Healthcare

Consumer Defensive

Financial Services

Utilities

👉 Le secteur est crucial, car le Moat est évalué relativement au secteur.

🔹 MoatRaw

Score brut moyen calculé sur les 5 dernières années

Basé sur :

rentabilité opérationnelle

génération de free cash flow

marges

ROE

intensité R&D

discipline en capital (CapEx)

levier financier

📌 Ce score n’est pas normalisé et ne doit pas être comparé entre secteurs.

👉 Il sert uniquement de base de calcul interne.

🔹 MoatPercentile ⭐ (colonne la plus importante)

Percentile du Moat au sein du secteur

Échelle : 0 à 100

Valeur	Interprétation
90–100	Avantage concurrentiel très fort (dominant)
75–90	Moat solide
50–75	Qualité moyenne
< 50	Peu ou pas d’avantage durable

👉 Exemple :
MoatPercentile = 92
➡️ l’entreprise est dans le top 8 % de son secteur en termes de moat.

🔹 MoatTrend

Pente de l’évolution du score brut dans le temps

Calculée par régression linéaire sur 5 ans

Valeur	Signification
> 0	amélioration du moat
≈ 0	stabilité
< 0	détérioration

👉 Sert à détecter :

l’expansion d’un moat

ou son érosion progressive

🔹 MoatLabel

Interprétation qualitative de la tendance

Label	Signification
🟢 Expansion	Moat en amélioration
🟡 Stable	Moat relativement stable
🔴 Érosion	Moat en dégradation
🔹 CoreHolding (si présent)

Booléen (True / False)

Indique si le titre répond aux critères de cœur de portefeuille long terme

Critère typique :

MoatPercentile ≥ 90

tendance positive ou stable

🧠 Philosophie du modèle
Pourquoi un score relatif ?

Le S&P 500 est déjà composé d’entreprises de qualité.
Un score absolu tend donc à regrouper artificiellement les entreprises.

👉 Le Moat est par nature relatif :

une entreprise a un avantage seulement si elle est structurellement meilleure que ses concurrents.

Pourquoi par secteur ?

Les modèles économiques sont très différents :

un ROE de 15 % est banal en technologie

exceptionnel dans les utilities

👉 Comparer uniquement à l’intérieur d’un secteur est indispensable.

Pourquoi long terme (5 ans) ?

Un moat :

n’est pas une photo annuelle

se construit et se maintient dans le temps

👉 Le score est basé sur la moyenne et la stabilité sur plusieurs années.

🎯 Cas d’usage typiques

Sélection de Core Holdings long terme

Construction d’un portefeuille Core / Satellite

Filtrage d’univers avant analyse fondamentale

Contenu éducatif (Discord, formation, long terme)

⚠️ Limites connues

Dépendance aux données Yahoo Finance (qualité variable)

Ne remplace pas une analyse qualitative (marque, réseau, switching costs)

Le MoatScore ne prédit pas la performance à court terme

📌 Conclusion

Ce scanner n’identifie pas simplement les « bonnes entreprises ».
Il met en évidence celles qui possèdent un avantage concurrentiel durable,
relativement à leur secteur,
et cohérent dans le temps.

👉 C’est un outil d’aide à la décision long terme, pas un signal de trading.
