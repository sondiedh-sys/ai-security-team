# AI Security Team

Une équipe d'agents Claude (sous-agents Claude Code) qui réalise un audit de sécurité en boîte blanche : scanner statique, testeur dynamique, orchestrateur qui vérifie les constats, recalcule les scores CVSS et rédige un rapport PDF.

![Audit en cours : le testeur attaque l'app qui tourne](docs/img/captures/03-pentest-dynamique-live.png)

## Ce que l'expérience a montré

Quatre audits sur deux apps (une soignée, une générée en un seul prompt), avec l'équipe puis un seul prompt naïf :

| | Équipe | Un seul prompt |
|---|---|---|
| `app_naive` (simple) | 10 constats, 2 élevés | 12 constats, 2 élevés |
| `App_muscu` (complexe) | 19 constats, 0 élevé | 10 constats, 0 élevé |

L'app soignée n'a aucun constat élevé ; l'app bâclée en a deux. Sur du code simple, un bon prompt suffit ; l'écart en faveur de l'équipe se creuse avec la complexité, surtout en couverture et en rigueur vérifiable. Détail et limites : [`docs/COMPARAISON.md`](docs/COMPARAISON.md).

## Contenu

- [`teams/`](teams/) : le code des équipes (agents, calcul CVSS, modèle de rapport). Adaptable à d'autres domaines.
- [`docs/`](docs/) : [documentation](docs/DOCUMENTATION.md), [comparaison](docs/COMPARAISON.md), [journal de bord](docs/journal_de_bord.md).
- [`reports/`](reports/) : rapports réels (équipe en PDF, baseline en Markdown) pour comparer.

## Limites

Rapports produits par des agents, vérifiés par l'orchestrateur mais pas par un auditeur humain. Tests dynamiques uniquement sur des stacks locales.

Licence MIT.
