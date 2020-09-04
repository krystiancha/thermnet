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
const margin = {top: 20, right: 15, bottom: 30, left: 30};


// Global objects

// const plot24h = createPlot(d3.select("#plot24h").attr("viewBox", [0, 0, width, height]), "24 h", true);
// const plot48h = createPlot(d3.select("#plot48h").attr("viewBox", [0, 0, width, height]), "48 h");
// const plot1w = createPlot(d3.select("#plot1w").attr("viewBox", [0, 0, width, height]), "tydzień");


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

    document.querySelector("#temperature #value").innerHTML = rawData.temperature.toFixed(1);
    document.querySelector("#humidity #value").innerHTML = rawData.humidity.toFixed(1);
    document.querySelector("#pressure #value").innerHTML = rawData.pressure.toFixed(1);
    console.log("Updated current temperature");

    setStatusBar(Status.UPDATING);

    // const data = rawData.data.data.map((value, index) => ({index: rawData.data.index[index], data: value}));

    // if (rawData.type === "24h") {
    //   updatePlot(plot24h, "%H:%M", data);
    //   console.log("Updated 24h plot");
    // } else if (rawData.type === "48h") {
    //   updatePlot(plot48h, "%H:%M", data);
    //   console.log("Updated 48h plot");
    // } else if (rawData.type === "1w") {
    //   updatePlot(plot1w, "%a", data);
    //   console.log("Updated 1w plot");
    // }
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

function createPlot(svg, title, minmax=false) {
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
      .attr("stroke", "#6c71c4")
      .attr("stroke-width", 1.5)
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
