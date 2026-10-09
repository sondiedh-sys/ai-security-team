# Équipe d'agents d'audit — version généralisée (réutilisable)

Version **indépendante d'une app précise** (contrairement à la version `../app_muscu/`,
câblée pour `App_muscu`). Cible par défaut : app web **Next.js + Supabase**.

## Contenu attendu dans `.claude/` de l'app à auditer

```
.claude/
├── agents/
│   ├── referentiel.md        (fourni ici)
│   ├── scanner.md            (fourni ici)
│   ├── pentester.md          (fourni ici)
│   ├── orchestrateur.md      (fourni ici)
│   ├── cvss31.py             (fourni ici)
│   └── rapport_modele.tex    (fourni ici)
└── audit/
    └── referentiel_owasp.md  (fourni ici)
```

## Lancer un audit sur une app

1. Copier le dossier `.claude/` ci-dessus dans la racine de l'app à auditer .
2. L'app doit tourner en **local** (Supabase local + serveur de dev), jamais sur un hôte `*.supabase.co`.
3. Ouvrir Claude Code dans le dossier de l'app et demander :
   > « Lance l'orchestrateur pour auditer cette application. »
4. Le rapport sort dans `rapports/audit_<date>.pdf`.

## Prérequis outils (dans la session d'audit)

`semgrep`, `gitleaks`, `tectonic` (compilation LaTeX), `curl`, Python 3. `npm audit` vient avec npm.

## Note anti-biais

Ces prompts ciblent la **stack** (Next.js + Supabase), pas les failles d'une app donnée. Ils n'ont
pas été écrits en regardant le code de `app_naive`, pour que l'audit reste un vrai test et non une
liste de réponses connues d'avance.
