// bot-ansv/static/js/login.js
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = e.target.email.value.trim();
  const mensaje = document.getElementById("mensaje");
  mensaje.textContent = "Enviando código...";

  console.log("Enviando código a:", email);
  const res = await fetch("/auth/enviar-codigo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });

  const data = await res.json();
  mensaje.textContent = data.message;
  if (res.ok) {
    setTimeout(() => {
      window.location.href = "/validar-codigo?email=" + encodeURIComponent(email);
    }, 1500);
  }
});
