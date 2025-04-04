const price_from = document.getElementById('price_from');
const price_from_value = document.getElementById('price_from_value');
const price_to = document.getElementById('price_to');
const price_to_value = document.getElementById('price_to_value');

price_from.addEventListener('input', () => {
    price_from_value.textContent = price_from.value;
});

price_to.addEventListener('input', () => {
    price_to_value.textContent = price_to.value;
}); 
