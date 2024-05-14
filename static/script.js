function updateQuantity(input) {
    var qty = input.value;
    var productLine = input.getAttribute('productLine');
    var formData = new FormData();
    formData.append('qty', qty);
    formData.append('productLine', productLine);

    fetch('/updateCart', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            // Update the line total on the frontend based on the response
            return response.json(); // Assuming the server sends back the updated line total and total cart value as JSON
        } else {
            throw new Error('Failed to update quantity');
        }
    })
    .then(data => {
        // Find the corresponding <td> element for the line total and update its content
        var lineTotalElement = document.getElementById('lineTotal' + productLine);
        if (lineTotalElement) {
            lineTotalElement.innerText = data.updatedLineTotal;
        }

        // Update the cart total value
        var cartTotalElement = document.getElementById('cartTotal');
        if (cartTotalElement) {
            cartTotalElement.value = data.updatedCartTotal;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
