document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('customerForm');
    const button = document.getElementById('checkout');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show sending message
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        button.disabled = true;
        
        try {
            // Get form data
            const formData = new FormData();
            formData.append("description", document.getElementById("description").value);
            formData.append("caption", document.getElementById("cedula").value);
            formData.append("image", document.getElementById("customerImage").files[0]);

            await fetch("/dashboard/save_forms/", {
            method: "POST",
            body: formData, // no Content-Type header, browser sets it automatically
        });

        // Success: reset form
        form.reset();
        alert("Data sent successfully!");
            
        } catch (error) {
            alert('Error sending data');
        }
        
        // Reset button
        button.innerHTML = '<i class="fas fa-save me-2"></i>Save Post';
        button.disabled = false;
    });
});