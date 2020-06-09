// Types

const Status = Object.freeze({
  "CONNECTING": 1,
  "WAITING_FOR_DATA": 2,
  "UPDATING": 3,
  "RECONNECTING": 4,
});


// Constants

const width = 300;
const height = 145;
const margin = {top: 20, right: 10, bottom: 30, left: 30};


// Global objects

const plot24h = createPlot(d3.select("#plot24h").attr("viewBox", [0, 0, width, height]), "24 h");
const plot48h = createPlot(d3.select("#plot48h").attr("viewBox", [0, 0, width, height]), "48 h");
const plot1w = createPlot(d3.select("#plot1w").attr("viewBox", [0, 0, width, height]), "tydzień");


// Main

setStatusBar(Status.CONNECTING);
connectSocket(`ws://${window.location.host}/ws/`);


// Functions

function connectSocket(url) {
  const webSocket = new WebSocket(url);

  webSocket.onopen = event => {
    console.log("WebSocket is open now:", event);
    setStatusBar(Status.WAITING_FOR_DATA);
  };

  webSocket.onmessage = function (event) {
    console.log("WebSocket message received:", event);
    document.getElementById("lastUpdated").innerHTML = (new Date).toLocaleTimeString();

    const rawData = JSON.parse(event.data);
    console.log("Data parsed:", rawData);

    if (rawData.type === "last") {
      document.getElementById("currentValue").innerHTML = rawData.data.toFixed(1);
      console.log("Updated current temperature");
      return;
    }

    setStatusBar(Status.UPDATING);

    const data = rawData.data.data.map((value, index) => ({index: rawData.data.index[index], data: value}));

    if (rawData.type === "24h") {
      updatePlot(plot24h, "%H:%M", data);
      console.log("Updated 24h plot");
    } else if (rawData.type === "48h") {
      updatePlot(plot48h, "%H:%M", data);
      console.log("Updated 48h plot");
    } else if (rawData.type === "1w") {
      updatePlot(plot1w, "%a", data);
      console.log("Updated 1w plot");
    }
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

function createPlot(svg, title) {
  svg.append("text")
    .attr("x", width / 2)
    .attr("y", margin.top / 2)
    .attr("text-anchor", "middle")
    .attr("font-size", "0.5em")
    .attr("fill", "#657b83")
    .text(title)
  return {
    x: d3.scaleTime().range([margin.left, width - margin.right]),
    y: d3.scaleLinear().range([height - margin.bottom, margin.top]),
    xAxis: svg.append("g").attr("transform", `translate(0,${height - margin.bottom})`),
    yAxis: svg.append("g").attr("transform", `translate(${margin.left}, 0)`),
    line: svg.append("path")
      .attr("fill", "none")
      .attr("stroke", "#268bd2")
      .attr("stroke-width", 1.5)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round"),
  }
}

function updatePlot(plot, timeFormat, data) {
    plot.x.domain(d3.extent(data, d => d.index));
    plot.y.domain(d3.extent(data, d => d.data)).nice();

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
          return plot.x(d.index);
        })
        .y(d => {
          return plot.y(d.data);
        }));
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
