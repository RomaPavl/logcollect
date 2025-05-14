document.addEventListener('DOMContentLoaded', () => {
    const refreshUrl = '/refresh';
    fetch(refreshUrl).then(() => console.log('Data refreshed'));
});