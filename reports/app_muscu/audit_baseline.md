# Audit de sécurité — baseline — App Muscu (Coach)

- **Date** : 2026-10-09
- **Périmètre audité** : branche `001-muscu-nutrition-coach`
- **Auditeur** : revue statique (manuelle) du code source et de la configuration
- **Type** : audit baseline (état de référence), boîte blanche, sans test d'intrusion dynamique

---

## 1. Résumé exécutif

Le projet est une application iOS native (SwiftUI / SwiftData) adossée à un backend Supabase
(Auth, Postgres + RLS, Edge Functions Deno/TypeScript) et à l'API Claude d'Anthropic, appelée
exclusivement côté serveur. La sécurité est traitée comme une exigence produit, pas comme une
finition, et cela se voit : l'architecture est saine et plusieurs classes de vulnérabilités
courantes sont évitées par conception.

**Posture globale : bonne.** Aucune vulnérabilité critique ou élevée exploitable n'a été identifiée
dans le code. Les points relevés sont majoritairement d'ordre durcissement / hygiène opérationnelle.

Points forts majeurs :

- **RLS activée sur 100 % des tables applicatives**, chaque ligne rattachée à `auth.uid()`, avec
  vérification de la propriété du parent sur les tables filles (`workout_sets`, `training_days`).
- **Test automatisé d'accès croisé** (`tests/rls_test.ts`) qui prouve l'isolation entre comptes,
  l'impossibilité d'écrire `ai_usage` directement, et le bon fonctionnement de la suppression de compte.
- **Sorties de l'IA considérées comme non fiables** et systématiquement revalidées côté serveur
  (schéma + règles métier + bornes) avant d'être renvoyées au client.
- **Aucun secret embarqué dans l'app** : seuls l'URL du projet et la clé publiable (publishable) sont
  présents côté client ; la clé secrète Supabase n'est utilisée que par `delete-account`.
- **Quota IA non manipulable par le client** : limites codées en dur dans une fonction
  `security definer`, jamais passées en paramètre.
- **Journalisation sans contenu** : les Edge Functions ne loggent que des durées et des codes de
  raison, jamais le texte utilisateur ni les réponses du modèle.

| Sévérité | Nombre |
|---|---|
| Critique | 0 |
| Élevée | 0 |
| Moyenne | 2 |
| Faible | 4 |
| Informationnel | 4 |

---

## 2. Périmètre et méthodologie

### Surfaces examinées

| Surface | Fichiers clés |
|---|---|
| Authentification / parsing requêtes | `supabase/functions/_shared/auth.ts` |
| Validation entrées + revalidation sorties IA | `supabase/functions/_shared/validate.ts`, `review.ts` |
| Appel modèle | `supabase/functions/_shared/claude.ts` |
| Handlers Edge Functions | `coach-workout`, `coach-command`, `coach-review`, `delete-account` |
| Schéma + RLS + RPC quota | `supabase/migrations/0001`→`0007` |
| Tests d'isolation | `tests/rls_test.ts` |
| Client iOS (auth, service, API) | `SupabaseService.swift`, `AuthView.swift`, `CoachAPI.swift` |
| Configuration / secrets | `.gitignore`, `ios/Config.xcconfig`, `supabase/functions/.env`, `.env.test`, `ios/project.yml` |
| Scripts | `scripts/fetch-exercise-images.sh` |

### Méthode

- Lecture intégrale du code backend (Deno/TS) et des migrations SQL.
- Revue des politiques RLS et des `grant`/`revoke`.
- Analyse de la chaîne de confiance entre le client, les Edge Functions, Postgres et le modèle.
- Recherche de secrets dans l'arbre de travail **et dans tout l'historique git** (`git log --all -p`).
- Analyse des vecteurs d'injection (SQL, prompt injection, command injection).

### Hors périmètre / limites

- Pas de test dynamique (DAST) ni de pentest sur l'instance Supabase déployée.
- La configuration du tableau de bord Supabase (politiques d'authentification, rate limits, protection
  mots de passe compromis, confirmation e-mail) n'est pas dans le dépôt : elle n'a donc **pas** pu être
  vérifiée et fait l'objet de recommandations.
- Pas de revue des dépendances tierces (CVE) ni du code Swift de logique métier (Progression, Stats…)
  côté sécurité, ces surfaces étant locales à l'appareil.

---

## 3. Constats détaillés

### M-1 — (Moyen) Clé API Anthropic réelle présente dans l'arbre de travail

- **Fichier** : `supabase/functions/.env`
- **Constat** : le fichier contient une clé Anthropic de type `sk-ant-usr-…` en clair. Elle est de
  type **utilisateur** (`usr`), généralement rattachée à un compte individuel plutôt qu'à un espace de
  travail cloisonné.
- **Bon point** : le fichier est correctement couvert par `.gitignore` (`.env*`) et **n'apparaît nulle
  part dans l'historique git** (vérifié). Il n'y a donc pas de fuite dans le dépôt.
- **Risque** : exposition locale (sauvegardes, partage de dossier, synchronisation cloud du poste, vol
  de machine). Une clé `usr` compromise peut engendrer des coûts et, selon le compte, un périmètre plus
  large qu'une clé d'espace de travail dédiée.
- **Recommandations** :
  1. En production, ne jamais s'appuyer sur ce fichier : définir la clé via les *secrets* des Edge
     Functions (`supabase secrets set`). Le `.env` local ne sert qu'au dev.
  2. Préférer une clé **d'espace de travail (workspace) à budget/plafond limité** plutôt qu'une clé
     utilisateur.
  3. **Rotation** de la clé si elle a pu transiter par un canal non sûr (copier-coller, capture, partage
     d'écran, ce rapport). Révoquer l'ancienne.

### M-2 — (Moyen) Politiques d'authentification Supabase non versionnées / non vérifiables

- **Constat** : il n'y a pas de `supabase/config.toml` dans le dépôt. Les garde-fous d'authentification
  critiques vivent donc uniquement dans le tableau de bord Supabase et ne sont ni audités ni reproductibles :
  - `verify_jwt` par fonction (bien que le code fasse une défense en profondeur, voir ci-dessous) ;
  - politique de longueur / complexité des mots de passe côté serveur (le client exige ≥ 8 caractères,
    mais c'est contournable en appelant l'API directement) ;
  - protection contre les mots de passe compromis (HIBP) ;
  - confirmation d'e-mail obligatoire ;
  - rate limiting et CAPTCHA sur `signUp`/`signIn` (anti-bruteforce / anti-création massive).
- **Atténuation existante** : `requireUser()` **re-vérifie systématiquement le JWT** via
  `auth.getUser(token)` au lieu de se fier à l'en-tête, donc même un `verify_jwt` désactivé par erreur
  ne donnerait pas accès non authentifié. C'est une bonne défense en profondeur.
- **Recommandations** :
  1. Versionner `supabase/config.toml` avec `verify_jwt = true` explicite pour chaque fonction (sauf si
     une fonction publique est voulue, ce qui n'est pas le cas ici).
  2. Dans le tableau de bord : activer la confirmation d'e-mail, la protection mots de passe compromis,
     une longueur minimale ≥ 8 (idéalement 10), et vérifier les rate limits d'auth.
  3. Documenter ces réglages dans le README (section Sécurité) pour qu'ils fassent partie de la baseline.

### F-1 — (Faible) Le quota IA est consommé avant l'appel au modèle

- **Fichier** : `coach-workout/index.ts`, `coach-command/index.ts`, `coach-review/index.ts`
- **Constat** : `consumeQuota()` incrémente le compteur **avant** l'appel à Claude. Si l'appel échoue
  (panne API, timeout) ou si la sortie est rejetée par la revalidation (`422`), le quota journalier de
  l'utilisateur est quand même décompté.
- **Risque** : il s'agit d'un contrôle de coût, pas d'un contrôle de sécurité. L'impact est une légère
  dégradation d'expérience (auto-DoS du quota) en cas d'erreurs répétées, non exploitable par un tiers.
  C'est aussi un choix défensif : consommer d'abord empêche d'épuiser l'API sous charge.
- **Recommandation** : acceptable en l'état. Si l'UX le justifie, ne décompter qu'en cas de succès (mais
  en gardant une protection contre les abus de ré-essai).

### F-2 — (Faible) Contraintes de format `exercise_key` posées en `NOT VALID`

- **Fichier** : `supabase/migrations/0007_exercise_key_format.sql`
- **Constat** : les contraintes de format sur `workout_sets.exercise_key` et
  `performance_goals.exercise_key` sont ajoutées en `NOT VALID` : elles s'appliquent aux lignes
  nouvelles/modifiées mais ne re-scannent pas l'existant.
- **Risque** : faible — les migrations indiquent que l'app est récente (pas de données de prod) et la
  valeur est de toute façon bornée en longueur et validée côté application. Le risque résiduel est un
  `exercise_key` historique mal formé qui persisterait.
- **Recommandation** : une fois confirmé qu'aucune ligne non conforme n'existe, exécuter
  `ALTER TABLE … VALIDATE CONSTRAINT …` pour durcir et garantir l'invariant sur tout le jeu de données.

### F-3 — (Faible) Script `fetch-exercise-images.sh` : valeurs injectées dans URL/chemins

- **Fichier** : `scripts/fetch-exercise-images.sh`
- **Constat** : le script lit `key` et `source_id` depuis `exercises.json` et les interpole dans un
  chemin de destination (`$DEST/$key`) et une URL (`$BASE/$source/...`). La source est un fichier du
  dépôt (de confiance), donc le risque est théorique, mais une valeur contenant `../` ou des caractères
  spéciaux pourrait provoquer une écriture hors du dossier cible.
- **Risque** : faible (entrée de confiance, exécution manuelle ponctuelle par le développeur).
- **Recommandation** : valider `key`/`source` contre une liste blanche de caractères
  (`^[a-z0-9_]+$` / `^[A-Za-z0-9_ -]+$`) avant utilisation, par cohérence avec le reste du projet qui
  valide tout.

### F-4 — (Faible) Longueur minimale du mot de passe appliquée seulement côté client

- **Fichier** : `ios/Coach/Features/Auth/AuthView.swift` (`password.count >= 8`)
- **Constat** : la règle des 8 caractères est une validation d'UI ; elle n'est pas opposable à un client
  modifié appelant directement l'API Supabase Auth.
- **Risque** : faible, mais réel si aucune politique serveur n'est configurée (voir M-2).
- **Recommandation** : définir la longueur minimale et la protection mots de passe compromis dans la
  configuration Supabase Auth (couvre ce point et F-4 d'un coup).

### I-1 — (Info) Absence d'en-têtes CORS sur les Edge Functions

- **Constat** : les fonctions renvoient du JSON sans en-têtes CORS. Pour un client **natif iOS**, c'est
  sans impact et même préférable (pas de surface navigateur). À noter uniquement si un client web devait
  être ajouté plus tard : il faudrait alors une origine explicitement allowlistée (jamais `*` avec
  credentials).

### I-2 — (Info) `.env.example` whitelisté mais absent

- **Constat** : `.gitignore` fait `!.env.example` mais le fichier n'existe pas. C'est cosmétique ; un
  `.env.example` (avec valeurs factices) aiderait à documenter les variables attendues sans risque.

### I-3 — (Info) Robustesse de l'anti-prompt-injection

- **Constat** : le texte utilisateur et les « faits » sont envoyés comme **données**, avec une consigne
  explicite de ne pas exécuter d'instructions qu'ils contiendraient, et surtout **toute sortie du modèle
  est revalidée** : schéma zod, clés limitées au catalogue, zones sensibles retirées, bornes de séries,
  nombres du bilan obligatoirement issus des faits (`checkReview`), filtrage URL + mots interdits. Le
  modèle n'a **aucun outil** et ne décide ni des charges ni du volume. C'est l'implémentation de
  référence attendue : le risque de prompt injection menant à une action non voulue est maîtrisé. Point
  noté comme **force**, pas comme faiblesse.

### I-4 — (Info) Données de santé stockées (poids corporel, zones douloureuses)

- **Constat** : `profiles.bodyweight_kg`, `workouts.pain_zone`, `energy` sont des données personnelles à
  caractère de santé. La suppression de compte en cascade (`ON DELETE CASCADE` + `delete-account`) couvre
  bien le droit à l'effacement. À garder en tête pour la conformité RGPD (base légale, information de
  l'utilisateur, minimisation) si l'app est publiée.

---

## 4. Points forts confirmés (ce qui est bien fait)

- **Isolation multi-comptes prouvée par test** : `tests/rls_test.ts` vérifie lecture/écriture/
  suppression croisées impossibles sur **toutes** les tables, l'impossibilité de forger une ligne au nom
  d'un autre, l'impossibilité d'attacher un `workout_set`/`training_day` à un parent d'autrui, et le rejet
  des écritures directes dans `ai_usage`.
- **Quota non falsifiable** : `consume_ai_quota` est `security definer`, `set search_path = ''`, avec des
  limites codées en dur ; `execute` révoqué pour `public`/`anon`. Un appel REST ne peut pas relever son
  propre quota.
- **`delete-account` minimal et correct** : seule fonction détentrice de la clé secrète, agit uniquement
  sur l'appelant **vérifié**, révoque toutes les sessions (`signOut global`) avant suppression.
- **Validation d'entrée stricte** : `z.strictObject` partout (rejet des champs inconnus), bornes
  numériques, énumérations, longueurs max — côté Edge Functions **et** répliquées en contraintes CHECK /
  `valid_template_items` dans la base, de sorte qu'un client modifié écrivant directement en base ne peut
  rien stocker que l'app n'autoriserait.
- **Pas de fuite de secret** dans l'app (seule la clé publiable y figure) ni dans l'historique git.
- **Messages d'erreur génériques** : pas d'énumération de comptes à l'authentification, pas de détails
  internes renvoyés (`invalid_input`, `unauthorized`), logs serveur sans contenu utilisateur.
- **Clés étrangères protégées explicitement** : les politiques RLS d'insertion/màj vérifient la propriété
  du parent (une FK ne passe pas par la RLS), piège classique correctement traité.

---

## 5. Plan d'action priorisé

| # | Action | Sévérité | Effort |
|---|---|---|---|
| 1 | Confirmer que la clé Anthropic n'est utilisée qu'en *secret* de fonction en prod ; la faire tourner si elle a pu fuiter ; préférer une clé workspace plafonnée (M-1) | Moyen | Faible |
| 2 | Versionner `supabase/config.toml` (`verify_jwt=true`) et verrouiller la politique Auth (longueur mdp, HIBP, confirmation e-mail, rate limits) + la documenter (M-2, F-4) | Moyen | Faible |
| 3 | `VALIDATE CONSTRAINT` sur les `exercise_key` une fois l'existant vérifié (F-2) | Faible | Faible |
| 4 | Valider `key`/`source` dans le script d'images (F-3) | Faible | Faible |
| 5 | (Option) Ne décompter le quota qu'en cas de succès (F-1) | Faible | Faible |
| 6 | Ajouter un `.env.example` ; préparer la doc RGPD si publication (I-2, I-4) | Info | Faible |

---

## 6. Conclusion

Pour un projet portfolio affiché comme « la sécurité fait partie du produit », l'engagement est tenu
côté code : isolation des données, défiance vis-à-vis du modèle, non-exposition des secrets et tests
d'accès croisés constituent une base solide. **Aucun défaut critique ou élevé n'a été trouvé dans le
code.** Les deux points moyens relèvent de l'hygiène opérationnelle (gestion de la clé API, mise en
dépôt et verrouillage de la configuration d'authentification Supabase) plus que d'un défaut de
conception, et se corrigent rapidement.

> *Cet audit est statique et ne remplace pas un test d'intrusion dynamique sur l'instance déployée ni
> une revue de la configuration réelle du projet Supabase, recommandés avant toute mise en production
> publique.*
