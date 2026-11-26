document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById("checkPriority");
    const result = document.getElementById("priorityResult");
    const endpoint = button.dataset.url;

    button.addEventListener("click", function () {
        const severity = document.getElementById("id_severity").value;
        const description = document.getElementById("id_description").value;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({ severity: severity, description: description })
        })
        .then(response => response.json().then(data => ({
            status: response.status,
            data: data
        })))
        .then(({ status, data }) => {
            result.style.display = "block";
            if (status !== 200) {
                result.className = "alert alert-danger";
                result.textContent = data.error || "Request failed.";
                return;
            }
            result.className = "alert alert-success";
            result.textContent = "Suggested Priority: " + data.suggested_priority;
        })
        .catch(error => {
            result.style.display = "block";
            result.className = "alert alert-danger";
            result.textContent = "Unable to contact server.";
            console.error(error);
        });
    });
});
