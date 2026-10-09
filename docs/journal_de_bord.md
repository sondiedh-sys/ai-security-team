# Journal de bord — AI Security Team

Document rempli au fur et à mesure : ce qu'on fait, les choix faits, et leur justification. Objectif : garder une trace raisonnée du projet (utile pour le CV/GitHub et pour comprendre plus tard *pourquoi* telle décision).

---

## 2026-09-23 — Naissance du projet

**Décision : nouveau projet prioritaire, homelab en pause.**
Justification : Doudou veut construire un vrai système agentique (IA + cyber), ce qui l'intéresse davantage que la suite du homelab VM pour l'instant. Le homelab n'est pas abandonné, juste mis de côté (Kerberoasting laissé en cours de dépannage).

**Décision : concept = une "équipe de sécurité" d'agents Claude auditant une app cobaye.**
Justification : double apprentissage — (1) concevoir une architecture multi-agents (rôles, outils, accès de chacun), (2) s'entraîner à la sécurité applicative en la voyant appliquée. Rôles de base retenus : scanner (analyse statique), pentester dynamique (test de l'app en fonctionnement), orchestrateur/rédacteur (centralise, priorise, rédige le rapport). Modèle inspiré de la chaîne collecteur/mapper/redacteur déjà existante.

**Décision : l'app cobaye embarquera elle-même une fonctionnalité IA.**
Justification : très courant aujourd'hui (assistant connecté par API + règles). Ça ajoute une surface d'audit moderne et alignée avec l'axe "sécurité IA" de Doudou : prompt injection, fuite de données sensibles, contournement des règles données à l'IA.

**Décision : app containerisée avec Docker.**
Justification : coller aux pratiques réelles de dev et faire pratiquer Docker (compétence attendue partout).

**Décision : protocole de comparaison plutôt qu'un simple audit unique.**
Justification : rend l'exercice bien plus riche à documenter/montrer. Quatre approches à comparer :
1. Review "brute" — un seul prompt à Claude sur l'app finie. Référence basse.
2. Audit structuré par l'équipe d'agents.
3. Retrofit — pass "sécurise cette app" a posteriori sur l'app déjà terminée.
4. Conception guidée (App B) — même app reconstruite avec un skill sécurité dès le départ, puis même audit d'agents.
Croise deux axes : conception naïve vs guidée, et review rapide vs audit structuré vs retrofit.

---

## 2026-09-24 — Répartition des rôles et anti-biais

**Décision : Doudou construit l'app cobaye (App A) lui-même, dans une conversation séparée.**
Justification : éviter tout biais — cette session (et donc les agents de sécu qu'on va concevoir ici) ne doit pas connaître le code de l'app à l'avance. Ça reproduit un vrai test en boîte noire, où l'équipe d'audit découvre l'application sans en avoir écrit une ligne. Délai estimé : quelques jours.

**Conséquence : le rôle de cette session = guider la conception/implémentation de l'équipe d'agents**, pas l'app.

**Décision : suppression du scaffold Next.js/Supabase commencé le 2026-09-23.**
Justification : c'était un exemple préliminaire choisi par Claude ; Doudou construit la vraie app lui-même. On repart propre pour ne pas mélanger.

---

## 2026-10-04 — Architecture de l'équipe verrouillée

**Décision : environnement = Claude Code en terminal (CLI), dans le dépôt de l'app.**
Justification : les sous-agents `.claude/agents/*.md` sont une fonctionnalité native du CLI, c'est le terrain canonique pour apprendre à les construire. L'app desktop (Cowork) sait déléguer mais n'est pas l'endroit pour *construire* l'équipe. Les agents vivent dans `.claude/agents/` du dépôt de l'app (pour lire le code sur place) ; `ai_secteam/` reste le classeur (conception, journal, rapports).

**Décision : première équipe = orchestrateur + 2 ouvriers (scanner, pentester).**
Justification : l'orchestrateur n'est pas un 4e fichier — c'est la session Claude Code elle-même : tu dis "audite l'app", elle appelle scanner puis pentester, ramasse les constats et rédige le rapport. Les agents en plus (dépendances, secrets, remédiation) attendront que la boucle à 2 ouvriers soit rodée (pas de dispersion).

**Décision : viser une équipe RÉALISTE et réutilisable, pas un jouet local.**
Justification / cadrage conceptuel :
- De vrais outils externes : les agents lancent les outils standards du métier (semgrep, nuclei, sqlmap, gitleaks, npm audit, OWASP ZAP, advisors Supabase). L'IA orchestre et interprète, les outils détectent. C'est le paradigme de l'audit assisté par IA actuel.
- Modèle d'engagement = **audit en boîte blanche / test authentifié** : accès complet au code + projet Supabase + identifiants, comme une équipe sécu interne ou un cabinet mandaté. C'est un vrai type de mission (vs boîte noire = sans accès).
- Réutilisabilité : l'équipe ne doit pas être codée en dur pour cette app. Garder la config légère pour qu'on puisse la pointer sur un autre dépôt + un autre Supabase sans rien changer. C'est ce qui la rend "réelle" et pas "collée à ma machine".
- Honnêtetés retenues : (a) une vraie mission commence par une autorisation écrite (scope / rules of engagement) — ici app perso, donc OK ; (b) les agents LLM ratent/hallucinent parfois → multiplicateur de force avec relecture humaine, pas confiance aveugle.

Guide pas-à-pas + `scanner.md` prêt à l'emploi : voir `guide_agents.md`.

---

## 2026-10-06 — Équipe d'agents construite et premier audit réalisé (vérifié)

Doudou a construit l'équipe dans `cyber/Projet/` (app auditée = `App_muscu/`, son app iOS perso : SwiftUI + Supabase — Postgres/RLS, Edge Functions Deno/TS, API Claude côté fonctions). Il est allé **au-delà des 3 agents prévus**.

**Ce qui a été construit (dans `Projet/.claude/agents/`) :**
- `scanner.md` — SAST : lecture intégrale + semgrep + gitleaks, matrice de couverture obligatoire, classification par référentiel + vecteur CVSS.
- `pentester.md` — DAST : teste la stack Supabase locale (REST/RLS, Edge Functions, prompt injection réelle sur les `coach-*`), avec **garde-fou anti-prod** (refuse tout hôte `*.supabase.co`), budget d'appels Claude.
- `orchestrateur.md` — lance referentiel → scanner → pré-check env → pentester, déduplique, **recalcule chaque CVSS et vérifie les dires des sous-agents**, rédige le rapport LaTeX, compile avec tectonic.
- `referentiel.md` (agent en plus) — remet à jour `.claude/audit/referentiel_owasp.md` depuis les sources OWASP officielles (API Top 10, LLM Top 10, MASVS, ASVS).
- `cvss31.py` — calcul du score CVSS 3.1 (pour ne jamais estimer à la main), `rapport_modele.tex` — gabarit du rapport.

**Vérification faite par Claude (ce que j'ai contrôlé moi-même, pas juste cru) :**
- `cvss31.py` : testé sur 3 vecteurs connus → 9.8 / 7.5 / 4.3, valeurs canoniques exactes. Formule CVSS 3.1 correcte.
- `referentiel_owasp.md` : éditions à jour (API 2023, LLM 2025, MASVS v2, ASVS 5.0.0).
- 3 constats recoupés avec le vrai code → **réels, pas hallucinés** : F-01 (delete-account n'exige que `confirm:"DELETE"`, pas de réauth), F-04 (RPC `valid_template_items` bien présent), F-09 (`ANTHROPIC_API_KEY` en clair dans `functions/.env`).
- Le test dynamique a **vraiment tourné** (stack locale 127.0.0.1:54321, 9 appels Claude réels sur 15, tests d'isolation A/B, garde-fou anti-prod respecté) — ce n'est pas du statique déguisé.
- L'orchestrateur a fait un **vrai travail de vérification** : il a corrigé 3 constats de ses sous-agents (clé Anthropic reclassée de 7.5 Élevée → Faible car `AV:N` injustifié pour un fichier local gitignoré ; fausse affirmation « dépendances épinglées » corrigée en « flottantes, pas de lockfile » ; sévérité des inscriptions ramenée de Moyenne → Faible car comportement local ≠ prod). Section « limites » honnête sur ce qui n'a pas été testé.

**Résultat de l'audit (`Projet/rapports/audit_2026-10-06.{tex,pdf}`, 4 itérations v1→v3 puis finale) :** 0 critique, 0 élevé, 2 moyens (F-01 suppression sans réauth, F-02 contraintes base incomplètes), 9 faibles, 8 info. Conclusion solide : la RLS et l'auth tiennent ; les constats sont du durcissement, pas des trous béants. Cohérent avec une app construite proprement (spec-kit).

**Verdict pédagogique :** c'est de la qualité de vrai rapport d'audit. L'architecture est réutilisable (pointer `.env.test` + `App_muscu/` ailleurs suffirait). Point d'attention à garder en tête : les tests de prompt injection ne prouvent pas l'absence de toute injection (modèle non déterministe), et la config Auth déployée n'est pas vérifiable sans `config.toml` — bien noté dans les limites.

**Où on en est du protocole de comparaison (tâche #22) :** ceci = l'étape 2 (audit structuré par l'équipe). Restent : étape 1 (review brute, un seul prompt — à faire pour comparer), étape 3 (retrofit « sécurise maintenant » a posteriori), étape 4 (App B conçue avec skill sécu dès le départ).

**Décision 2026-10-06 : pas d'App B guidée.** À la place, on créera d'autres agents (dépendances dédié, secrets dédié, remédiation ; plus tard SOC et réseau rebranchés sur le homelab).

**Précision importante sur App_muscu (relevée en documentant) :** ce n'est PAS l'« App A négligée » du plan initial. C'est une app conçue sécurité-d'abord (constitution spec-kit, RLS + test d'accès croisé A/B automatisé, JWT revérifié, quotas `security definer`, sortie IA revalidée, Keychain, l'IA ne décide jamais charges/reps). D'où le « 0 critique » : l'app tient parce qu'elle est bien bâtie. La valeur de l'audit ici = confirmer qu'une conception soignée résiste + remonter les durcissements, pas exhiber des trous. À formuler ainsi sur le GitHub (honnêteté).

**Documentation produite :** `DOCUMENTATION.md` (GitHub-ready) avec 4 schémas Mermaid (construction de l'app via spec-kit, archi d'exécution + frontières de sécurité, construction de la security team du choix des outils au moindre privilège, pipeline d'audit à l'exécution), plus les emplacements de captures et le protocole de baseline équitable.

**Décision 2026-10-06 (soir) : nouvelle expérience principale = contraste app soignée vs app bâclée.** Plutôt que de seulement comparer les méthodes d'audit sur `App_muscu`, on construit en plus une app **bâclée** (un seul prompt naïf, pas de spec, pas d'outils, pas de consigne sécu) et on audite les DEUX avec la même équipe. L'écart de constats démontre que la qualité de construction se mesure (méthode vs vibecoding). Condition clé : même stack et périmètre comparable (Next.js + Supabase : auth, données propres à l'utilisateur/RLS, une fonction IA) pour que l'écart vienne de la discipline, pas de la techno ; app bâclée construite pour de vrai (session neuve, un prompt), pas de failles plantées à la main. Ça remplace l'idée de "copier App_muscu ailleurs" : l'app bâclée EST la cible naïve. Axe secondaire bonus : sur l'app bâclée, comparer aussi audit par l'équipe vs audit en un seul prompt.

**2026-10-06 : diagrammes Excalidraw faits.** Les 4 schémas ont été régénérés en Excalidraw (skill coleam00/excalidraw-diagram) dans `Projet/docs/diagrams/` (`.excalidraw` éditables + `.png`) : `app-construction`, `app-architecture`, `secteam-construction`, `secteam-pipeline`. Vérifiés visuellement (rendu propre, le pipeline et le moindre privilège « racontent » bien). `DOCUMENTATION.md` a été basculé des blocs Mermaid vers ces PNG (chemin relatif `../Projet/docs/diagrams/`, valable si racine dépôt = `cyber/`).

**2026-10-06 : point publication GitHub.** Rien n'est publié pour l'instant (tout est en local ; « GitHub-ready » = rédigé pour publication, pas publié). État : `App_muscu` a déjà son dépôt `github.com/sondiedh-sys/app-muscu` (propre, aucun `.env` suivi). Le reste (équipe d'agents, rapports, diagrammes, `ai_secteam/`, `cv/`) n'est versionné nulle part. Décision : **on ne publie rien maintenant, on verra plus tard.** `App_muscu` restera peut-être **privée** (Doudou envisage de continuer l'app). En revanche, Doudou veut publier **les rapports, les architectures/diagrammes, les captures et les agents eux-mêmes (y compris leurs `.md`)**. Conséquences : (1) publier la version *généralisée* des agents (celle qu'on fera pour l'app bâclée), pas la version câblée pour `App_muscu` qui pointerait vers une app privée → la généralisation sert donc aussi à rendre les agents publiables ; (2) zéro secret dans le publié — le rapport évite les valeurs de clés, les agents ne citent que des chemins de `.env` (pas leur contenu), et le vrai `functions/.env` reste gitignoré dans `App_muscu`. Si publication un jour : repo dédié à l'équipe avec `Projet/` comme racine, en excluant `App_muscu/` (lien seulement), `mods-marketplace/` (plugins tiers → citer), `cv/` (numéro perso), et en ne gardant que le rapport final (pas v1/v2/v3). Point de sécu avant toute publication du rapport : corriger d'abord les 2 constats moyens ouverts (app publique), puis publier avec statut « corrigé ».

**2026-10-08 : méthode d'isolation pour le build bâclé.** Un dossier neutre ne suffit pas : tout ce qui est au niveau compte (`~/.claude/` : skill `pick-tools`, plugins scope `user`, MCP, CLAUDE.md perso) se charge dans toutes les sessions. Méthode retenue : dossier neutre hors `cyber/` (`~/Desktop/notes-app`) + `claude --safe-mode` (désactive CLAUDE.md, plugins, skills, hooks, MCP ; garde la connexion). Variante étanche : `CLAUDE_CONFIG_DIR=/tmp/claude-clean claude` (profil vierge, reconnexion requise). Vérification obligatoire avant le prompt : `/context`, `/mcp`, `/agents`, `/plugin` doivent être vides de tout outil perso. Assumé : le modèle garde son bon sens par défaut (il peut ajouter un peu de sécu de lui-même) — c'est réaliste et fait partie de la mesure ; on retire la discipline et l'outillage de Doudou, pas l'intelligence du modèle.

**2026-10-08 : app bâclée construite + agents généralisés.** L'app bâclée a été générée en one-shot (`claude --safe-mode`, prompt naïf) : `app_naive` dans `~/Documents/app_naive` — Next.js (App Router) + Supabase, auth/notes/partage/commentaires + assistant IA (route `/api/assistant` → Claude). Construite avec **Claude Opus 4.8 en reasoning high** (détail important : la cible n'est pas « un dev négligent » mais « un modèle capable, en one-shot, sans méthode ni outils »). Observation clé : **le modèle a mis de la sécurité tout seul** (RLS avec fonctions `SECURITY DEFINER`, maj Next.js vers version patchée) sans aucune consigne. Donc le contraste attendu « soignée vs pleine de trous » sera sans doute plus subtil ; la vraie question devient « que reste-t-il comme failles quand on se fie aux seuls réflexes par défaut de l'IA ? ». Tourne en local (Supabase local 127.0.0.1:54321, `npm run dev`) ; a demandé ~1h de friction juste pour faire marcher la création de note (donnée en soi sur les apps vibecodées).

Version **généralisée** des agents créée dans `ai_secteam/agents/` (scanner, pentester, orchestrateur réécrits pour cibler la stack Next.js+Supabase et n'importe quelle app, pas `App_muscu`) + README. C'est la version publiable. `referentiel.md`, `cvss31.py`, `referentiel_owasp.md`, `rapport_modele.tex` restent réutilisés tels quels depuis `Projet/.claude/`. Écrits sans lire le code de `app_naive` (anti-biais). Prochaine action : copier ce `.claude/` dans `app_naive/` et lancer l'orchestrateur.

**2026-10-09 : les 3 audits sont faits et comparés.** Résultats (crit/élevé/moyen/faible/info) : App_muscu équipe 0/0/2/9/8 ; app_naive équipe 0/2/4/3/1 ; app_naive baseline-1-prompt 0/2/4/4/2. Rapports dans `comparaison/`. Synthèse complète : `comparaison/COMPARAISON.md`.
- **Axe 1 (qualité de construction) : thèse confirmée.** app_naive, malgré sa RLS spontanée, a un trou d'autorisation Élevé (CVSS 8,3 : vol de propriété d'une note via `PATCH owner_id`, policy UPDATE sans restriction de colonne) qu'App_muscu avait fermé. Trouvé par les deux audits → réel.
- **Axe 2 (équipe vs 1 prompt) : résultat honnête et humble.** La baseline a trouvé les mêmes 2 constats majeurs + 2 que l'équipe a ratés (dérive config schema/snippets ; seed/secrets dev). L'équipe n'apporte pas plus de failles mais de la rigueur vérifiable (CVSS, OWASP, confirmation dynamique réelle de la prompt injection, matrice de couverture, rapport PDF). Conclusion : pour un modèle capable, un bon prompt trouve le gros ; l'orchestration achète rigueur/repro/confirmation dynamique, pas du volume.
- **Limite majeure (soulevée par Doudou) : la simplicité d'app_naive.** Petite app → un prompt tient tout le code en contexte, donc l'avantage d'échelle de l'orchestration ne s'exprime pas. Test de suivi pour trancher : lancer une baseline-1-prompt sur App_muscu (plus complexe) et voir si l'écart équipe-vs-prompt se creuse.
- **Amélioration agents identifiée** : le scanner a raté la dérive de config que la baseline a vue → lui faire inspecter `supabase/snippets/` et signaler les écarts schéma versionné vs déployé.
- **Action sécu** : révoquer/régénérer la clé Anthropic réelle qui traînait dans `app_naive/.env.local` (flaggée par les 2 audits).

**2026-10-09 (suite) : test de suivi fait — l'hypothèse de Doudou est validée.** Baseline-1-prompt sur `App_muscu` (safe-mode, Opus 4.8 high, prompt naïf) : 0/0/2/4/4 = 10 constats. Comparaison des totaux équipe-vs-prompt : app_naive (simple) 10 vs 12 (baseline +2) ; App_muscu (complexe) 19 vs 10 (équipe +9). **L'écart s'inverse et se creuse avec la complexité** → l'orchestration multi-agents paie à l'échelle, pas sur du code simple. Nuances honnêtes : le surplus équipe est surtout faibles/info (couverture), les deux trouvent 0 crit/0 élevé sur App_muscu (app solide, pas de gros trou à trouver → test incomplet), mais l'équipe a surfacé un moyen (delete-account sans réauth) que la baseline a raté. Détail dans `comparaison/COMPARAISON.md`. Rapport rangé : `comparaison/audit_baseline_appmuscu.md`. **Volet expérience bouclé.**

**2026-10-09 : captures faites et intégrées.** 12 captures dans `capture_audit_agent_comparaison/`. 6 retenues et renommées proprement (01-baseline-safe-mode, 02-orchestration-flow, 03-pentest-dynamique-live, 04-rapport-final [vignette générée du PDF], 05-baseline-safe-mode-appmuscu, 06-app_naive-ui). Galerie légendée ajoutée dans `DOCUMENTATION.md` §2.3. Les 7 autres (progression /flow) gardées en appoint. À noter : `06-app_naive-ui.png` contient un email de test → à flouter avant toute publication.

## À remplir ensuite
- (Idéal, si l'envie) refaire le test sur une app complexe ET réellement vulnérable, pour voir l'équipe attraper un vrai trou que le one-shot rate.
- ✅ Fait (2026-10-09) : clé Anthropic de `app_naive` régénérée ; email masqué dans 06-app_naive-ui.
- Améliorer le scanner (dérive de config `supabase/snippets/`).
- Nouveaux agents (dépendances, secrets, remédiation) — le volet prévu après celui-ci.
- Captures Claude Code (`/flow`, etc.) pour le GitHub.
- (Bonus) sur l'app bâclée : équipe structurée vs audit en un prompt (session isolée hors `cyber/`).
- Nouveaux agents (dépendances, secrets, remédiation).
- Captures Claude Code pour le GitHub (voir DOCUMENTATION.md §2.3).
