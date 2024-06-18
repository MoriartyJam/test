// static/script.js
function syncProducts() {
    document.getElementById("status").innerHTML = '<img src="https://i.gifer.com/YCZH.gif" alt="Loading"/>';
    fetch('/sync_products')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'finished') {
                document.getElementById("status").innerHTML = 'Sync process finished.';
            } else {
                document.getElementById("status").innerHTML = 'An error occurred during sync.';
            }
        })
        .catch(error => {
            document.getElementById("status").innerHTML = 'An error occurred during sync.';
        });
}
