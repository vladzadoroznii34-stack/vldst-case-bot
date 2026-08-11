const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

async function loadUser() {

    const initData = tg.initData;

    if (!initData) {
        console.log("VLDST: Mini App открыт не через Telegram");
        return;
    }

    try {

        const response = await fetch(
            "/api/user",
            {
                headers: {
                    "X-Telegram-Init-Data": initData
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            console.error(
                "VLDST API error:",
                data
            );
            return;
        }

        console.log(
            "VLDST USER:",
            data
        );

        updateInterface(data);

    } catch (error) {

        console.error(
            "VLDST connection error:",
            error
        );
    }
}


function updateInterface(user) {

    const coinsElement =
        document.getElementById("coins");

    const starsElement =
        document.getElementById("stars");

    if (coinsElement) {
        coinsElement.textContent =
            Number(user.coins).toLocaleString("ru-RU");
    }

    if (starsElement) {
        starsElement.textContent =
            user.stars;
    }

    const logo =
        document.querySelector(".logo small");

    if (logo) {

        const name =
            user.first_name || "PLAYER";

        logo.textContent =
            `WELCOME, ${name.toUpperCase()}`;
    }
}


function openCase() {

    const notification =
        document.getElementById(
            "notification"
        );

    notification.textContent =
        "🎁 Система кейсов скоро будет доступна!";

    notification.classList.add(
        "show"
    );

    setTimeout(() => {

        notification.classList.remove(
            "show"
        );

    }, 2500);
}


loadUser();
