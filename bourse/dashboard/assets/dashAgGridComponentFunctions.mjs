var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

function handleColorRenderer(value) {
    if (isNaN(value)) {
        return "NaN";
    }
    if (value === 0) {
        return "0%";
    }
    if (value > 0) {
        return `↑ ${value.toFixed(2)}%`;
    }
    return `↓ ${value.toFixed(2)}%`;
}

dagcomponentfuncs.colorRenderer = function (props) {
    var value = parseFloat(props.value);
    return React.createElement("span", {
        style: {
            color: isNaN(value) ? "#5c5c5c" : value >= 0 ? "#46E372" : "#FF005C",
            fontWeight: "400",
            backgroundColor: isNaN(value) ? "#5c5c5c30" : value >= 0 ? "#46E3721A" : "#FF005C30",
            borderRadius: "20px",
            padding: "5px 12px",
        }
    }, handleColorRenderer(value));
};

dagcomponentfuncs.stockLink = function (props) {
    var symbol = props.value;
    return React.createElement(
        'a',
        {
            href: 'https://boursorama.com/cours/' + symbol,
            target: '_blank',
            style: {
                color: "#007BFF",
                textDecoration: "none",
            }
        },
        props.value
    );
};