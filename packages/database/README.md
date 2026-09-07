# Configuration de la base de données SûrCheck AI (Supabase)

Ce dossier contient les définitions et migrations SQL officielles pour SûrCheck AI.

## Fichiers :
1. [`schema.sql`](file:///c:/S%C3%BBrCheck/packages/database/schema.sql) : Les 12 tables officielles, énumérations, index et contraintes.
2. [`seeds.sql`](file:///c:/S%C3%BBrCheck/packages/database/seeds.sql) : Règles initiales déterministes et scénarios réels documentés pour le Bénin et l'Afrique de l'Ouest.

## Déploiement sur Supabase :
1. Rendez-vous sur votre dashboard Supabase : [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Créez un nouveau projet (ex: `surcheck-ai-dev`).
3. Ouvrez le **SQL Editor** dans le menu latéral gauche.
4. Copiez et collez le contenu de `schema.sql` et cliquez sur **Run**.
5. Copiez et collez le contenu de `seeds.sql` et cliquez sur **Run**.
6. Récupérez vos clés d'API (Project Settings > API) et votre chaîne de connexion Postgres (Project Settings > Database > Connection string URI) pour les renseigner dans vos fichiers `.env`.
