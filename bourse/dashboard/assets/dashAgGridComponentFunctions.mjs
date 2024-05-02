var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.colorRenderer = function (props) {
    var value = parseFloat(props.value);
    return React.createElement("span", {
        style: {
            color: value >= 0 ? "#46E372" : "#FF005C",
            fontWeight: "400",
            backgroundColor: value >= 0 ? "#46E3721A" : "#FF005C30",
            borderRadius: "20px",
            padding: "5px 12px",
        }
    }, `${value > 0 ? '↑' : (value < 0 ? '↓' : '')} ${value.toFixed(2)}%`);
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