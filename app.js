document.addEventListener('DOMContentLoaded', () => {
    const submitButton = document.getElementById('submit-btn');
    const clearButton = document.getElementById('clear-btn');

    submitButton.addEventListener('click', async () => {
        const query = document.getElementById('query').value;

        if (!query) {
            alert('Please enter a description');
            return;
        }

        const response = await fetch('/query', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });

        const data = await response.json();
        displayAnimeRecommendations(data);
    });

    clearButton.addEventListener('click', () => {
        document.getElementById('query').value = '';
        const animeBlocks = document.querySelectorAll('.anime-block');
        animeBlocks.forEach(block => block.innerHTML = '');
    });

    function displayAnimeRecommendations(data) {
        const animeBlocks = document.querySelectorAll('.anime-block');
        data.forEach((anime, index) => {
            animeBlocks[index].innerHTML = `
                <h3>${anime.name}</h3>
                <img src="${anime.image}" alt="Anime Image">
                <p>${anime.description}</p>
                <button>👍 Like</button>
                <button>👎 Dislike</button>
            `;
        });
    }
});
