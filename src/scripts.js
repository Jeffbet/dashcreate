document.addEventListener("DOMContentLoaded", function() {
    // Carrossel de Imagens para Landing Page
    const carouselContainer = document.querySelector('.carousel-container');
    const slides = document.querySelectorAll('.carousel-slide');
    let currentIndex = 0;

    function showNextSlide() {
        currentIndex = (currentIndex + 1) % slides.length;
        const translateXValue = -(currentIndex * 100);
        carouselContainer.style.transform = `translateX(${translateXValue}%)`;
    }

    setInterval(showNextSlide, 3000); // Transição a cada 3 segundos

    // Funções do Modal de Importação no Index
    const importButton = document.getElementById("importButton");
    const exportButton = document.getElementById("exportButton");
    const importModal = document.getElementById("importModal");
    const closeModal = document.getElementById("closeModal");
    const generateButton = document.getElementById("generateButton");
    const fileInput = document.getElementById("fileInput");

    // Função para abrir o modal de importação
    importButton.addEventListener("click", function() {
        importModal.style.display = "block";
    });

    // Função para fechar o modal de importação
    closeModal.addEventListener("click", function() {
        importModal.style.display = "none";
    });

    // Fechar modal se clicar fora dele
    window.addEventListener("click", function(event) {
        if (event.target === importModal) {
            importModal.style.display = "none";
        }
    });

    // Submeter o formulário de importação
    generateButton.addEventListener("click", function(event) {
        if (fileInput.files.length === 0) {
            alert('Por favor, selecione um arquivo CSV.');
            event.preventDefault(); // Impede o envio do formulário se não houver arquivo
        }
    });

    // Cookie Consent Modal
    const cookieConsentModal = document.getElementById("cookieConsentModal");
    const acceptCookiesButton = document.getElementById("acceptCookies");
    const declineCookiesButton = document.getElementById("declineCookies");

    function showCookieConsent() {
        cookieConsentModal.style.display = "block";
    }

    function hideCookieConsent() {
        cookieConsentModal.style.display = "none";
    }

    acceptCookiesButton.addEventListener("click", function() {
        document.cookie = "user_accepts_cookies=yes; path=/; max-age=" + 60 * 60 * 24 * 365;
        hideCookieConsent();
    });

    declineCookiesButton.addEventListener("click", function() {
        document.cookie = "user_accepts_cookies=no; path=/; max-age=" + 60 * 60 * 24 * 365;
        hideCookieConsent();
    });

    if (document.cookie.indexOf("user_accepts_cookies") === -1) {
        showCookieConsent();
    }
});
