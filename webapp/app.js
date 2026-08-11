let coins = 0;
let stars = 0;

function openCase() {
    const notification = document.getElementById("notification");

    notification.textContent = "🎁 Скоро здесь будет настоящее открытие кейса!";
    notification.classList.add("show");

    setTimeout(() => {
        notification.classList.remove("show");
    }, 2500);
}
