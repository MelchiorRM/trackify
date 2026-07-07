# Dev-mode image (Vite dev server) — matches the local workflow used through
# Phase 5. Phase 6 (launch readiness) should replace this with a production
# multi-stage build (vite build -> static files served by nginx) — see
# appPlan.txt DEVELOPMENT PHASES, Phase 6.
FROM node:20-alpine

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
