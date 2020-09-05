const Status = Object.freeze({
  "CONNECTING": 1,
  "WAITING_FOR_DATA": 2,
  "UPDATING": 3,
  "RECONNECTING": 4,
});

const width = 300;
const height = 145;
const margin = {top: 20, right: 15, bottom: 30, left: 40};

const plotTemperature = createPlot(d3.select("#plotTemperature").attr("viewBox", [0, 0, width, height]), "Temperatura [°C] (ostatnie 24 h)", "#dc322f");
const plotHumidity = createPlot(d3.select("#plotHumidity").attr("viewBox", [0, 0, width, height]), "Wilgotność względna [%] (ostatnie 24 h)", "#859900");
const plotPressure = createPlot(d3.select("#plotPressure").attr("viewBox", [0, 0, width, height]), "Ciśnienie atmosferyczne [hPa] (ostatnie 24 h)", "#268bd2");

function connectSocket(url) {
  const webSocket = new WebSocket(url);

  webSocket.onopen = event => {
    console.log("WebSocket is open now:", event);
    setStatusBar(Status.WAITING_FOR_DATA);
  };

  webSocket.onmessage = function (event) {
    console.log("WebSocket message received:", event);
    document.getElementById("lastUpdated").innerHTML = (new Date).toLocaleTimeString();

    const data = JSON.parse(event.data);
    console.log("Data parsed:", data);

    document.getElementById("temperatureValue").innerHTML = data[0].measurements.slice(-1)[0].value.toFixed(1);
    document.getElementById("humidityValue").innerHTML = data[2].measurements.slice(-1)[0].value.toFixed(1);
    document.getElementById("pressureValue").innerHTML = data[1].measurements.slice(-1)[0].value.toFixed(1);
    console.log("Updated current temperature");

    updatePlot(plotTemperature, "%H:%M", data[0].measurements)
    updatePlot(plotHumidity, "%H:%M", data[2].measurements)
    updatePlot(plotPressure, "%H:%M", data[1].measurements)

    setStatusBar(Status.UPDATING);
  }

  webSocket.onclose = event => {
    console.log("Websocket connection was closed:", event);
    setStatusBar(Status.RECONNECTING);
    setTimeout(() => { connectSocket(url); }, 1000);
  };

  webSocket.onerror = event => {
    console.error("WebSocket error observed:", event);
  };
}

function createPlot(svg, title, color, minmax=false) {
  svg.append("text")
    .attr("x", width / 2)
    .attr("y", margin.top / 2)
    .attr("text-anchor", "middle")
    .attr("font-size", "0.5em")
    .attr("fill", "#657b83")
    .text(title)

  const plot = {
    x: d3.scaleTime().range([margin.left, width - margin.right]),
    y: d3.scaleLinear().range([height - margin.bottom, margin.top]),
    xAxis: svg.append("g").attr("transform", `translate(0,${height - margin.bottom})`),
    yAxis: svg.append("g").attr("transform", `translate(${margin.left}, 0)`),
    line: svg.append("path")
      .attr("fill", "none")
      .attr("stroke", color)
      .attr("stroke-width", 1.0)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round"),
  }

  if (minmax) {
    plot.minLine = svg.append("line")
      .attr("fill", "none")
      .attr("stroke", "#268bd2")
      .attr("stroke-width", 0.5);

    plot.minText = svg.append("text")
    .attr("text-anchor", "end")
    .attr("dy", -2)
    .attr("font-size", "0.5em")
    .attr("fill", "#657b83")

    plot.maxLine = svg.append("line")
      .attr("fill", "none")
      .attr("stroke", "#cb4b16")
      .attr("stroke-width", 0.5);

    plot.maxText = svg.append("text")
    .attr("text-anchor", "end")
    .attr("dy", -2)
    .attr("font-size", "0.5em")
    .attr("fill", "#657b83")
  }

  return plot
}

function updatePlot(plot, timeFormat, data) {
    plot.x.domain([new Date - 24 * 3600 * 1000, new Date()]);
    plot.y.domain(d3.extent(data, d => d.value)).nice();

    plot.xAxis
      .call(
        d3.axisBottom(plot.x)
          .ticks(8)
          .tickSizeOuter(0)
          .tickFormat(d3.timeFormat(timeFormat))
      )
      .call(g => g.select(".domain").remove());
    plot.yAxis
      .call(d3.axisLeft(plot.y).ticks(5))
      .call(g => g.selectAll(".tick line")
        .clone()
        .attr("stroke-opacity", d => d === 1 ? null : 0.2)
        .attr("x2", width - margin.left - margin.right))
      .call(g => g.select(".domain").remove());

    plot.line
      .datum(data)
      .attr("d", d3
        .line()
        .x(d => {
          return plot.x(d.index * 1000);
        })
        .y(d => {
          return plot.y(d.value);
        }));

    if ("minLine" in plot && "minText" in plot && "maxLine" in plot && "maxText" in plot) {
      const yMin = Math.min(...data.map(x => x.data));
      plot.minLine
        .attr("x1", margin.left)
        .attr("x2", width)
        .attr("y1", plot.y(yMin))
        .attr("y2", plot.y(yMin));

      plot.minText
        .attr("x", width)
        .attr("y", plot.y(yMin))
        .text(yMin.toFixed(1));

      const yMax = Math.max(...data.map(x => x.data));
      plot.maxLine
        .attr("x1", margin.left)
        .attr("x2", width)
        .attr("y1", plot.y(yMax))
        .attr("y2", plot.y(yMax));

      plot.maxText
        .attr("x", width)
        .attr("y", plot.y(yMax))
        .text(yMax.toFixed(1));
    }
}

function setStatusBar(status) {
  if (status === Status.CONNECTING) {
    document.getElementById("connectingStatus").classList.remove("hidden");
    document.getElementById("waitingForDataStatus").classList.add("hidden");
    document.getElementById("updatingStatus").classList.add("hidden");
    document.getElementById("reconnectingStatus").classList.add("hidden");
  } else if (status === Status.WAITING_FOR_DATA) {
    document.getElementById("connectingStatus").classList.add("hidden");
    document.getElementById("waitingForDataStatus").classList.remove("hidden");
    document.getElementById("updatingStatus").classList.add("hidden");
    document.getElementById("reconnectingStatus").classList.add("hidden");
  } else if (status === Status.UPDATING) {
    document.getElementById("connectingStatus").classList.add("hidden");
    document.getElementById("waitingForDataStatus").classList.add("hidden");
    document.getElementById("updatingStatus").classList.remove("hidden");
    document.getElementById("reconnectingStatus").classList.add("hidden");
  } else if (status === Status.RECONNECTING) {
    document.getElementById("connectingStatus").classList.add("hidden");
    document.getElementById("waitingForDataStatus").classList.add("hidden");
    document.getElementById("updatingStatus").classList.add("hidden");
    document.getElementById("reconnectingStatus").classList.remove("hidden");
  }
}