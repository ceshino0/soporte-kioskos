# Publicar el proyecto en GitHub (con GitHub Desktop)

La entrega admite ZIP **o** repositorio público. Estos pasos publican la carpeta como repo nuevo.

## 1. Preparar la carpeta
1. Descomprime `soporte-kioskos.zip` en tu carpeta de proyectos, por ejemplo
   `C:\Users\<tu-usuario>\Documents\Personal\Educacion\Claude\`.
2. Comprueba que ves la carpeta `.claude` (está oculta por el punto): en el Explorador,
   **Vista → Mostrar → Elementos ocultos**.

## 2. Crear el repositorio
1. Abre **GitHub Desktop** → **File → Add local repository…**
2. Elige la carpeta `soporte-kioskos`. Dirá que *no es un repositorio Git*: pulsa
   **create a repository**.
3. Nombre: `soporte-kioskos`. Deja **Git ignore: None** y **License: None**
   (el proyecto ya trae su `.gitignore`). Pulsa **Create repository**.

## 3. Revisar antes del primer commit
En la pestaña **Changes** verifica que:
- ✅ aparecen `.claude/skills/...`, `.claude/settings.json`, `.mcp.json`, `mcp-server/`, `docs/`.
- ❌ **no** aparecen `.venv/`, `*.db`, `audit.log` ni ningún `.env` (el `.gitignore` los excluye).
  Si ves alguno, no hagas commit y revisa el `.gitignore`.

Mensaje de commit: `Proyecto final: Skill triage-kioskos + MCP kioskos` → **Commit to main**.

## 4. Publicar
1. Pulsa **Publish repository**.
2. **Desmarca "Keep this code private"**: el campus necesita poder abrirlo.
3. **Publish repository**.

## 5. Comprobar y entregar
1. **Repository → View on GitHub**. Revisa que el `README.md` se ve con el diagrama
   (GitHub renderiza Mermaid automáticamente).
2. Copia la URL (`https://github.com/<tu-usuario>/soporte-kioskos`) y pégala en la
   actividad **"Entrega de proyecto final"** del campus. Si lo prefieres, sube también el ZIP.
