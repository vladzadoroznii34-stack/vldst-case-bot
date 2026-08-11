const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;

if (user) {
    console.log("VLDST USER:", user);

    const firstName = user.first_name || "Player";

    const logo = document.querySelector(".logo small");

    if (logo) {
        logo.textContent = `WELCOME, ${firstName.toUpperCase()}`;
    }
}

function openCase() {
    const notification = document.getElementById("notification");

    notification.textContent =
        "🎁 Система кейсов скоро будет доступна!";

    notification.classList.add("show");

    setTimeout(() => {
        notification.classList.remove("show");
    }, 2500);
}
