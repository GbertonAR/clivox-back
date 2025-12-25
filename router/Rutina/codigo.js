// bot-ansv/static/js/codigo.js
document.getElementById("codigo-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const urlParams = new URLSearchParams(window.location.search);
  const email = urlParams.get("email");
  const codigo = e.target.codigo.value.trim().toUpperCase(); // mayúsculas
  const mensaje = document.getElementById("mensaje");
  mensaje.textContent = "Validando...";

  try {
    const res = await fetch("/auth/validar-codigo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, codigo })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      mensaje.textContent = "✅ Código correcto. Redirigiendo...";
      
      // Guardar cookie manualmente si no se hizo en backend
      document.cookie = `usuario_id=${data.usuario_id}; path=/; max-age=86400`;

      setTimeout(() => {
        window.location.href = data.redirect_url || "/";
      }, 1000);
    } else {
      mensaje.textContent = data.error || "❌ Código incorrecto.";
    }

  } catch (err) {
    console.error("Error al validar el código:", err);
    mensaje.textContent = "❌ Error de red. Inténtalo nuevamente.";
  }
});
