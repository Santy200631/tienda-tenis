// Espera a que el documento este listo antes de activar interacciones compartidas.
document.addEventListener("DOMContentLoaded", () => {
    // Cierra automaticamente los mensajes temporales para mantener la interfaz limpia.
    document.querySelectorAll(".alert[data-autohide='true']").forEach((alertElement) => {
        window.setTimeout(() => {
            if (window.bootstrap) {
                const instance = window.bootstrap.Alert.getOrCreateInstance(alertElement);
                instance.close();
            } else {
                alertElement.remove();
            }
        }, 4500);
    });

    // Aplica una animacion suave cuando las tarjetas entran al viewport.
    const revealCards = document.querySelectorAll(".reveal-card");
    if ("IntersectionObserver" in window && revealCards.length > 0) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.18 }
        );

        revealCards.forEach((card) => observer.observe(card));
    } else {
        revealCards.forEach((card) => card.classList.add("is-visible"));
    }

    // Controla los botones de cantidad del detalle de producto.
    document.querySelectorAll("[data-qty-target]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.qtyTarget);

            if (!input) {
                return;
            }

            const currentValue = parseInt(input.value || "1", 10);
            const minValue = parseInt(input.min || "1", 10);
            const maxValue = parseInt(input.max || "999", 10);
            const delta = button.dataset.qtyAction === "increase" ? 1 : -1;
            const nextValue = Math.max(minValue, Math.min(maxValue, currentValue + delta));

            input.value = nextValue;
        });
    });
});
