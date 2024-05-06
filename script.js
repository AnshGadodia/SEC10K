function navigateToVisualization() {
    var selectedCompany = document.getElementById("companySelect").value;
    window.location.href = "visualization.html?ticker=" + selectedCompany;
}