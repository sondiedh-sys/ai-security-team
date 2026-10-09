# Comparaison des audits — ce que l'expérience démontre

Expérience : auditer deux applications de même stack (Supabase + IA) mais de **qualité de construction opposée**, et comparer aussi deux **méthodes d'audit** (équipe d'agents vs un seul prompt).

- **App soignée** : `App_muscu` (iOS + Supabase), construite avec méthode (spec-kit, sécurité pensée dès le départ).
- **App bâclée** : `app_naive` (Next.js + Supabase), générée en one-shot par un Claude vierge (Opus 4.8, reasoning high), un seul prompt naïf, sans spec ni consigne de sécurité.

## Résultats

| | App_muscu (soignée) · équipe | app_naive (bâclée) · équipe | app_naive · baseline (1 prompt) |
|---|---|---|---|
| Critique | 0 | 0 | 0 |
| Élevé | **0** | **2** | **2** |
| Moyen | 2 | 4 | 4 |
| Faible | 9 | 3 | 4 |
| Info | 8 | 1 | 2 |

Constat Élevé phare de `app_naive` (trouvé par les DEUX audits, donc réel) : un collaborateur avec un partage « édition » peut **s'approprier une note** (`PATCH owner_id`) car la policy UPDATE ne restreint aucune colonne. `App_muscu` ne l'avait pas : elle vérifiait explicitement l'appartenance des lignes liées par clé étrangère.

## Axe 1 — la qualité de construction se mesure (thèse principale : confirmée)

Même en mettant de la RLS toute seule, l'app bâclée laisse un **trou d'autorisation de gravité Élevée** (CVSS 8,3) que l'app soignée a fermé. Ce n'est pas « plein de trous vs zéro » : c'est « les cas limites d'autorisation (immuabilité de colonnes, appartenance des FK) que la discipline attrape et que le one-shot laisse ouverts ». Le fait que les deux audits trouvent ce trou indépendamment le valide.

## Axe 2 — équipe d'agents vs un seul prompt (résultat honnête, et nuancé)

La baseline (un prompt, zéro agent, zéro outil) s'en sort **remarquablement bien** : mêmes deux constats majeurs que l'équipe, **plus** deux choses que l'équipe a ratées (dérive de config `schema.sql` vs snippets ; identifiants de seed / secrets de dev local), avec des correctifs en code.

Ce que l'équipe apporte en plus n'est **pas plus de failles**, c'est de la **rigueur vérifiable** : vecteurs CVSS calculés (vs emojis), classification OWASP, **confirmation dynamique réelle** (prompt injection testée et confirmée, pas seulement supposée), matrice de couverture, couche de vérification, rapport PDF défendable.

**Conclusion :** pour un modèle capable, un seul bon prompt trouve déjà le gros. L'orchestration multi-agents achète la rigueur, la reproductibilité, la confirmation dynamique et un rapport défendable — pas un volume de constats supérieur. C'est ce qui sépare un cabinet d'audit d'un dev qui lance un outil.

## Limite importante de l'axe 2 : la simplicité de `app_naive`

`app_naive` est petite (~4 tables, quelques routes, un endpoint IA). Un Claude en un prompt tient **toute la base dans son contexte** et raisonne en une passe — il ne rate presque rien parce qu'il n'y a presque rien à rater. Or le bénéfice d'une équipe multi-agents est de gérer **l'échelle** (gros dépôt, division du travail, couverture exhaustive) ; sur une app aussi petite, cet avantage ne peut pas s'exprimer. Donc le résultat « la baseline fait aussi bien » est probablement **expliqué en grande partie par la simplicité de l'app**, pas par une absence de valeur de l'orchestration.

Nuances qui tiennent quand même, indépendamment de la taille : la confirmation dynamique et la rigueur/reproductibilité ne dépendent pas de la taille de l'app ; et le constat raté par l'équipe (dérive de config) est un problème de *périmètre du prompt du scanner*, pas de taille.

## Test de suivi (fait le 2026-10-09) : la complexité creuse-t-elle l'écart ? → OUI

Baseline en un prompt lancée sur `App_muscu` (même conditions que celle d'`app_naive` : `--safe-mode`, Opus 4.8 high, prompt naïf). Résultat `App_muscu` baseline : 0 crit / 0 élevé / 2 moyens / 4 faibles / 4 info = **10 constats**.

Écart équipe vs un seul prompt, par app (nombre total de constats) :

| | Équipe | Baseline (1 prompt) | Écart |
|---|---|---|---|
| **app_naive** (simple) | 10 | 12 | baseline +2 |
| **App_muscu** (complexe) | **19** | 10 | **équipe +9** |

**L'écart s'inverse et se creuse avec la complexité.** Sur l'app simple, le prompt seul faisait aussi bien (voire mieux) ; sur l'app complexe, l'équipe trouve presque le double. L'hypothèse « simplicité » est confirmée : le bénéfice de l'orchestration multi-agents est faible sur une petite base (un bon modèle en une passe suffit) et croît avec la complexité du code.

Lecture honnête (ne pas sur-vendre) :
- Le surplus de l'équipe sur `App_muscu` est surtout en **faibles/info** (9+8 contre 4+4) — de la *couverture exhaustive* (matrice de couverture), pas des trous graves en plus.
- **Les deux ont trouvé 0 critique / 0 élevé sur `App_muscu`** : l'app est réellement solide, il n'y avait pas de gros trou. Le test « l'équipe attrape-t-elle une vraie faille que le one-shot rate ? » n'a donc pas pu pleinement se jouer — il faudrait une app complexe **ET** vulnérable.
- Point qualitatif : l'équipe a surfacé un **moyen** (suppression de compte sans réauthentification) que la baseline a raté (elle a même qualifié `delete-account` de « correct »). La baseline, elle, a mieux cadré l'hygiène de la clé API. Donc pas d'écrasement, mais sur l'app complexe l'équipe a trouvé un moyen de plus.

**Conclusion générale (portfolio) :** l'apport de l'orchestration multi-agents est marginal sur du code simple (un bon modèle suffit) mais croît avec la complexité — en couverture, et parfois en profondeur. La rigueur vérifiable (CVSS, OWASP, confirmation dynamique, rapport) est un apport constant, indépendant de la taille.

## Amélioration identifiée pour les agents

Le scanner a raté la divergence `schema.sql` vs `supabase/snippets/` (dérive de config) que la baseline a vue. → Ajouter au scanner la consigne d'inspecter les fichiers de requêtes ad hoc et de signaler les dérives entre schéma versionné et état déployé.
