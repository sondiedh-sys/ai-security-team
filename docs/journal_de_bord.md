# Journal de bord — AI Security Team

Les étapes du projet, les choix faits et leur justification.

---

## 2026-09-23 — Naissance du projet

**Concept : une « équipe de sécurité » d'agents Claude qui audite une app cobaye.**
Double objectif : (1) concevoir une architecture multi-agents (rôles, outils, accès de chacun), (2) pratiquer la sécurité applicative en la voyant appliquée. Rôles de base : scanner (analyse statique), pentester dynamique (test de l'app en fonctionnement), orchestrateur/rédacteur (centralise, priorise, rédige le rapport).

**L'app cobaye embarque une fonctionnalité IA.**
C'est très courant aujourd'hui (assistant connecté par API + règles) et ça ajoute une surface d'audit moderne : prompt injection, fuite de données sensibles, contournement des règles données à l'IA.

**Protocole de comparaison plutôt qu'un audit unique.**
Comparer plusieurs approches (review en un seul prompt, audit structuré par l'équipe, etc.) rend l'expérience plus riche à mesurer et à documenter.

---

## 2026-09-24 — Anti-biais

**L'app cobaye est construite dans une session séparée.**
Les agents de sécurité ne doivent pas connaître le code de l'app à l'avance : l'équipe d'audit découvre l'application sans en avoir écrit une ligne.

---

## 2026-10-04 — Architecture de l'équipe

**Environnement : Claude Code en terminal, dans le dépôt de l'app.**
Les sous-agents `.claude/agents/*.md` sont une fonctionnalité native du CLI. Ils vivent dans le dépôt de l'app pour lire le code sur place.

**Première équipe : orchestrateur + 2 ouvriers (scanner, pentester).**
Les agents supplémentaires (dépendances, secrets, remédiation) attendront que cette boucle soit rodée.

**Une équipe réaliste et réutilisable, pas un jouet.**
- De vrais outils du métier : semgrep, gitleaks, npm audit, advisors Supabase… L'IA orchestre et interprète, les outils détectent.
- Modèle d'engagement : **audit en boîte blanche** (accès au code, au projet Supabase et à des identifiants de test), comme une équipe sécu interne ou un cabinet mandaté.
- Réutilisable : pas de configuration codée en dur pour une app précise.
- Limites assumées : une vraie mission commence par une autorisation écrite (ici, apps personnelles) ; les agents LLM peuvent rater ou halluciner, donc relecture humaine.

---

## 2026-10-06 — Équipe construite et premier audit (App_muscu)

Cible : `App_muscu`, une app iOS personnelle (SwiftUI + Supabase : Postgres/RLS, Edge Functions Deno/TS, API Claude côté fonctions).

**Ce qui a été construit :**
- `scanner.md` — SAST : lecture intégrale + semgrep + gitleaks, matrice de couverture obligatoire, classification par référentiel + vecteur CVSS.
- `pentester.md` — DAST : teste la stack Supabase locale (REST/RLS, Edge Functions, prompt injection réelle), avec **garde-fou anti-prod** (refuse tout hôte `*.supabase.co`) et budget d'appels Claude.
- `orchestrateur.md` — lance referentiel → scanner → pré-check env → pentester, déduplique, **recalcule chaque CVSS et vérifie les dires des sous-agents**, rédige le rapport LaTeX et le compile avec tectonic.
- `referentiel.md` — agent qui met à jour `referentiel_owasp.md` depuis les sources OWASP officielles (API Top 10, LLM Top 10, MASVS, ASVS).
- `cvss31.py` — calcul du score CVSS 3.1 (jamais d'estimation à la main) ; `rapport_modele.tex` — gabarit du rapport.

**Vérifications :**
- `cvss31.py` testé sur 3 vecteurs connus → 9.8 / 7.5 / 4.3, valeurs canoniques exactes.
- 3 constats recoupés avec le vrai code → réels, pas hallucinés.
- Le test dynamique a vraiment tourné (stack locale, appels Claude réels, tests d'isolation entre deux comptes, garde-fou anti-prod respecté).
- L'orchestrateur a corrigé 3 constats de ses sous-agents (un vecteur CVSS `AV:N` injustifié, une fausse affirmation sur l'épinglage des dépendances, une sévérité surestimée).

**Résultat :** 0 critique, 0 élevé, 2 moyens, 9 faibles, 8 info. La RLS et l'auth tiennent ; les constats relèvent du durcissement. Cohérent avec une app conçue sécurité d'abord (spec-kit, RLS testée, JWT revérifié, sortie IA revalidée, Keychain).

**Limites notées dans le rapport :** les tests de prompt injection ne prouvent pas l'absence de toute injection (modèle non déterministe), et la config Auth déployée n'est pas vérifiable en local.

**Nouvelle expérience principale : app soignée vs app bâclée.**
Construire en plus une app **bâclée** (un seul prompt naïf, sans spec, sans outils, sans consigne sécu) sur la même stack et un périmètre comparable, puis auditer les deux avec la même équipe. L'écart de constats doit montrer que la qualité de construction se mesure. Axe secondaire : sur l'app bâclée, comparer aussi l'équipe à un audit en un seul prompt.

---

## 2026-10-08 — App bâclée et agents généralisés

**Isolation du build bâclé.** Un dossier neutre ne suffit pas : tout ce qui est configuré au niveau du compte (skills, plugins, MCP, CLAUDE.md perso) se charge dans toutes les sessions. Méthode retenue : dossier hors du projet + `claude --safe-mode` (désactive CLAUDE.md, plugins, skills, hooks, MCP). Vérification avant le prompt : `/context`, `/mcp`, `/agents`, `/plugin` vides. Le modèle garde son bon sens par défaut, et c'est voulu : on retire la méthode et l'outillage, pas l'intelligence du modèle.

**`app_naive` construite en one-shot** : Next.js (App Router) + Supabase, auth / notes / partage / commentaires + assistant IA (`/api/assistant` → Claude). La cible n'est pas « un dev négligent » mais « un modèle capable, en one-shot, sans méthode ni outils ». Observation : le modèle a ajouté de la sécurité tout seul (RLS avec fonctions `SECURITY DEFINER`, Next.js à jour). La question devient : que reste-t-il comme failles quand on se fie aux seuls réflexes par défaut de l'IA ?

**Version généralisée des agents** (`teams/appsec/generic/`) : scanner, pentester et orchestrateur réécrits pour cibler la stack Next.js + Supabase de n'importe quelle app. Écrits sans lire le code de `app_naive` (anti-biais).

---

## 2026-10-09 — Audits et comparaison

Résultats (critique / élevé / moyen / faible / info) :

| Audit | Résultat |
|---|---|
| App_muscu — équipe | 0 / 0 / 2 / 9 / 8 |
| App_muscu — un seul prompt | 0 / 0 / 2 / 4 / 4 |
| app_naive — équipe | 0 / 2 / 4 / 3 / 1 |
| app_naive — un seul prompt | 0 / 2 / 4 / 4 / 2 |

- **Qualité de construction : thèse confirmée.** Malgré sa RLS spontanée, `app_naive` a un trou d'autorisation élevé (CVSS 8,3 : vol de propriété d'une note via `PATCH owner_id`, policy UPDATE sans restriction de colonne) qu'App_muscu avait fermé. Trouvé par les deux audits.
- **Équipe vs un seul prompt : résultat nuancé.** Sur `app_naive` (simple), le prompt unique trouve les mêmes constats majeurs, plus deux que l'équipe a ratés. Sur App_muscu (complexe), l'équipe trouve 19 constats contre 10, dont un moyen (suppression de compte sans réauthentification) que le prompt unique a raté. **L'avantage de l'orchestration apparaît avec la complexité** ; sur du code simple, elle apporte surtout de la rigueur vérifiable (CVSS recalculé, OWASP, confirmation dynamique, matrice de couverture, rapport PDF).
- **Amélioration identifiée :** le scanner a raté une dérive de configuration (schéma versionné vs déployé) vue par le prompt unique.

Détail et limites : [`COMPARAISON.md`](COMPARAISON.md). Rapports : [`reports/`](../reports/).

---

## Suite prévue

- Refaire le test sur une app complexe **et** réellement vulnérable.
- Améliorer le scanner (dérive de configuration Supabase).
- Nouveaux agents : dépendances, secrets, remédiation.
- Nouvelles équipes pour d'autres domaines (réseau).
