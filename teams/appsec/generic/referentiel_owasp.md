# Référentiel d'audit (lu par scanner, pentester et orchestrateur)

Dernière vérification : 2026-10-06 (sources consultées : API Security Top 10 2023, LLM Top 10 2025, MASVS v2, ASVS 5.0.0 ; chapitres ASVS non relus à la source)

Socle commun : chaque constat est classé avec ces référentiels, et chaque catégorie
doit apparaître dans la **matrice de couverture** du rapport (testé / non applicable
avec raison / non testé avec raison). « Je n'ai pas regardé » n'est pas « sans anomalie ».
Pour le détail d'une catégorie, consulte la source officielle (Context7 ou Firecrawl
si disponibles, sinon WebFetch) au lieu de citer de mémoire.

## 1. OWASP API Security Top 10 — 2023 (https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
Cible : REST Supabase (PostgREST) et Edge Functions.
- API1 Broken Object Level Authorization (IDOR, RLS entre utilisateurs)
- API2 Broken Authentication (JWT absent, expiré, forgé, session après suppression)
- API3 Broken Object Property Level Authorization (mass assignment, champs sensibles lisibles/écrivables)
- API4 Unrestricted Resource Consumption (quotas, coût IA, tailles de payload, comptes en série)
- API5 Broken Function Level Authorization (RPC et fonctions appelables par le mauvais rôle)
- API6 Unrestricted Access to Sensitive Business Flows (abus d'inscription, de quota, de suppression)
- API7 Server Side Request Forgery (URL fournies par l'utilisateur côté fonction)
- API8 Security Misconfiguration (CORS, en-têtes, config Auth, erreurs verbeuses, debug)
- API9 Improper Inventory Management (endpoints/versions oubliés, tables et RPC exposés)
- API10 Unsafe Consumption of APIs (confiance aveugle dans la réponse de Claude ou d'un tiers)

## 2. OWASP Top 10 for LLM Applications — 2025 (https://genai.owasp.org/llm-top-10/)
Cible : fonctions `coach-*` et appels à Claude.
- LLM01 Prompt Injection (directe et indirecte : champs libres, noms, historique)
- LLM02 Sensitive Information Disclosure (PII, données d'autres utilisateurs dans le contexte)
- LLM03 Supply Chain (SDK, modèles, dépendances `npm:`)
- LLM04 Data and Model Poisoning
- LLM05 Improper Output Handling (sortie du modèle utilisée sans validation, affichage, stockage)
- LLM06 Excessive Agency (outils, actions déclenchées par le modèle)
- LLM07 System Prompt Leakage
- LLM08 Vector and Embedding Weaknesses
- LLM09 Misinformation (conseils santé/entraînement dangereux, sorties non sourcées)
- LLM10 Unbounded Consumption (tokens, boucles, coût)

## 3. OWASP MASVS v2 (https://mas.owasp.org/MASVS/) — app iOS
Groupes : STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE, PRIVACY.
Tests associés : OWASP MASTG. Sans simulateur ni analyse de binaire, ces groupes
sont à marquer « revue de code seulement » ou « non testé ».

## 4. OWASP ASVS (https://owasp.org/www-project-application-security-verification-standard/)
Utiliser les chapitres authentification, gestion de session, contrôle d'accès,
validation des entrées, API et services web, configuration, journalisation.
Indiquer la version d'ASVS citée et vérifier la numérotation à la source avant de la citer.

## 5. Spécifique Supabase / Postgres (à vérifier systématiquement)
- RLS activée et forcée sur chaque table de `public`, politiques avec `(select auth.uid())`, pas de `using (true)`.
- `revoke` des droits à `anon`/`authenticated` là où inutile ; fonctions `security definer` avec `search_path` fixé.
- Colonnes JSON/texte libres sans contrainte (clé de validation côté base, pas seulement côté client).
- Clé secrète/service_role uniquement dans les fonctions qui en ont besoin, jamais côté client.
- Config Auth déployée (confirmation d'email, rate limits, durée des JWT) : à marquer « non vérifiable en local » si pas de config.toml.

## 6. Notation CVSS v3.1
- Fournir pour chaque constat le **vecteur** et le **score de base** (jamais un score estimé à la main) :
  `python3 .claude/agents/cvss31.py 'AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N'`
- Gravité du rapport = tranche CVSS : 0.1-3.9 Faible, 4.0-6.9 Moyenne, 7.0-8.9 Élevée, 9.0-10.0 Critique ; 0.0 = Info.
- Pour un risque qui n'a pas de score CVSS pertinent (abus de coût, hygiène de secrets locaux), dire
  « CVSS non pertinent » et justifier la gravité retenue.
- Une gravité reclassée (ex. Moyenne vers Faible) doit être justifiée par le vecteur, pas par un seul essai.
- Ne jamais citer un score, un identifiant CWE/CVE ou un numéro de contrôle sans l'avoir vérifié.
