# Équipes d'agents

Chaque dossier est une équipe pour un domaine. Elles partagent le même squelette (scanner → testeur dynamique → orchestrateur qui vérifie, score en CVSS et rédige) ; seuls la liste des surfaces, les outils et le référentiel changent.

| Équipe | Domaine | Statut |
|---|---|---|
| [`appsec/generic`](appsec/generic/) | Audit d'une app web (Next.js + Supabase par défaut, stack détectée) | Utilisable telle quelle |
| [`appsec/app_muscu`](appsec/app_muscu/) | Audit d'`App_muscu` (iOS + Supabase + Claude) | Version câblée pour une app précise |
| `network/` | Sécurité réseau / machines | Prévu |

## Différence `generic` vs `app_muscu`

- **`generic`** : cible « l'app du dossier courant », détecte la stack, critères larges. On copie `.claude/` dans n'importe quelle app (voir son README).
- **`app_muscu`** : périmètre en dur (chemins iOS/Swift, Edge Functions, règles santé de l'app). Plus précise sur cette app, à réécrire pour une autre.

## Adapter à un nouveau domaine

1. Garder les rôles et leurs droits minimaux (lecture seule pour le scanner, garde-fou « jamais en production » pour le testeur, outils complets seulement pour l'orchestrateur).
2. Réécrire la liste des surfaces d'attaque et les outils de chaque agent.
3. Remplacer le référentiel (`referentiel_owasp.md`) par celui du domaine.
4. Garder `cvss31.py`, la matrice de couverture et le modèle de rapport.
