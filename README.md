# TOM-CO-TCG-BOT

La branche **`main`** ne contient que ce dépôt minimal : le code applicatif (interface **TCG Scalper Pro**) vit sur la branche **`interface`**.

## Où est le code ?

- **Application (Vite + React)** : branche [`interface`](https://github.com/AnthonyNadjari/TOM-CO-TCG-BOT/tree/interface)

## Vercel

Les déploiements Git depuis **`main`** sont **ignorés** (`ignoreCommand` dans `vercel.json`) pour ne pas écraser la production avec une branche vide.

Pour que **chaque push** mette à jour **https://tom-co-tcg-bot.vercel.app** :

1. Dans Vercel : **Project → Settings → Git → Production Branch** → choisir **`interface`**.
2. (Optionnel) Sur GitHub : **Settings → General → Default branch** → **`interface`**, pour que les PR et clones ciblent l’app par défaut.

En attendant ce réglage, tu peux publier la prod depuis ta machine avec la branche `interface` :

```bash
git checkout interface
npx vercel deploy --prod --yes
```
