// static/script.js
document.getElementById("order-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const input = document.getElementById("order-input").value;
  const response = await fetch("/order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: input })
  });

  const result = await response.json();
  const output = result.items_extracted.map(item => 
    `<li>${item.quantity} × ${item.product}</li>`).join("");

  document.getElementById("result").innerHTML = `
    <h3>AI Extracted Items:</h3>
    <ul>${output}</ul>
  `;
});
