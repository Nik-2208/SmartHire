// main.js — God-Level Interactions
document.addEventListener("DOMContentLoaded", function() {

    /* ---------------- SKILL PILL INTERACTION ---------------- */
    const pills = document.querySelectorAll(".skill-pill");
    pills.forEach(pill => {
        pill.addEventListener("mouseenter", () => {
            pill.style.background = "rgba(0, 206, 201, 0.35)";
            pill.style.color = "#fff";
            pill.style.boxShadow = "0 0 15px rgba(0, 206, 201, 0.6)";
            pill.style.transform = "scale(1.1)";
        });

        pill.addEventListener("mouseleave", () => {
            pill.style.background = "rgba(0, 206, 201, 0.08)";
            pill.style.color = "#aaf8f8";
            pill.style.boxShadow = "inset 0 0 10px rgba(0, 206, 201, 0.1)";
            pill.style.transform = "scale(1)";
        });

        // Add a random floating animation delay for each pill
        const randomDelay = Math.random() * 5;
        pill.style.animationDelay = `${randomDelay}s`;
    });

    /* ---------------- BUTTON RIPPLE EFFECT ---------------- */
    const buttons = document.querySelectorAll("button");
    buttons.forEach(btn => {
        btn.style.position = "relative"; // Ensure ripple is positioned correctly
        btn.style.overflow = "hidden";   // Prevent ripple from overflowing

        btn.addEventListener("click", function (e) {
            const ripple = document.createElement("span");
            ripple.classList.add("ripple");
            this.appendChild(ripple);

            const rect = this.getBoundingClientRect();
            ripple.style.left = `${e.clientX - rect.left - 50}px`; // center ripple
            ripple.style.top = `${e.clientY - rect.top - 50}px`;

            setTimeout(() => ripple.remove(), 600);
        });
    });

    /* ---------------- 3D CARD INTERACTION ---------------- */
    const cards = document.querySelectorAll(".card");
    cards.forEach(card => {
        card.style.transition = "transform 0.2s ease"; // smooth reset

        card.addEventListener("mousemove", e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / 20) * -1;
            const rotateY = (x - centerX) / 20;

            card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.03)`;
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "rotateX(0deg) rotateY(0deg) scale(1)";
        });
    });

    /* ---------------- METRIC GLOW PULSE ---------------- */
    const metrics = document.querySelectorAll(".metric");
    setInterval(() => {
        metrics.forEach(metric => {
            metric.style.boxShadow = "0 0 20px rgba(0, 206, 201, 0.3)";
            metric.style.transform = "scale(1.05)";
            setTimeout(() => {
                metric.style.boxShadow = "inset 0 0 10px rgba(0, 206, 201, 0.05)";
                metric.style.transform = "scale(1)";
            }, 800);
        });
    }, 4000);

    /* ---------------- PARALLAX BACKGROUND FLOAT ---------------- */
    document.addEventListener("mousemove", (e) => {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;
        document.body.style.backgroundPosition = `${x * 30}px ${y * 30}px`;
    });

});

/* ---------------- EXTRA: CSS FOR RIPPLE ---------------- */
const rippleStyle = document.createElement("style");
rippleStyle.innerHTML = `
.ripple {
    position: absolute;
    background: rgba(255,255,255,0.6);
    border-radius: 50%;
    transform: scale(0);
    animation: rippleEffect 0.6s linear;
    pointer-events: none;
    width: 100px;
    height: 100px;
    opacity: 0.8;
}

@keyframes rippleEffect {
    to {
        transform: scale(4);
        opacity: 0;
    }
}`;
document.head.appendChild(rippleStyle);
