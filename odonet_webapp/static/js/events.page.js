/*
Events Page
*/

function onRootUpdate(updated) {

  if(updated.new_event || updated.page) {
    window.location.reload();
  }

}

let eventsConfig = {
  type: 'line',
  data: {
    datasets: [{
      label: 'Event Scores',
      backgroundColor: 'rgba(54, 162, 235, 0.5)',
      borderColor: 'rgb(54, 162, 235)',
      lineTension: 0,
      pointRadius: 1,
      fill: false,
      data: eventsData,
    }]
  },
  options: {
    responsive: true,
    title: {
      display: true,
      text: 'Events'
    },
    scales: {
      xAxes: [{
        type: 'time',
        display: true,
        scaleLabel: {
          display: true,
          labelString: 'Date'
        },
        ticks: {
          major: {
            fontStyle: 'bold'
          }
        }
      }],
      yAxes: [{
        display: true,
        scaleLabel: {
          display: true,
          labelString: 'scores'
        }
      }]
    }
  }
};

let radarConfig = {
  type: 'radar',
  data: {
    labels: deviceLabels,
    datasets: [
      {
        label: 'Past 2 Hours',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgb(255, 99, 132)',
        pointBackgroundColor: 'rgb(255, 99, 132)',
        data: radarLast2HoursData
      },
      {
        label: 'Past Day',
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgb(54, 162, 235)',
        pointBackgroundColor: 'rgb(54, 162, 235)',
        data: radarLastDayData
      },
      {
        label: 'Past Week',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgb(75, 192, 192)',
        pointBackgroundColor: 'rgb(75, 192, 192)',
        data: radarLastWeekData
      }
    ]
  },
  options: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Event Radar'
    },
    scale: {
      ticks: {
        beginAtZero: true
      }
    }
  }
};

let eventsCtx = document.getElementById('events-canvas').getContext('2d');
let eventsChart = new Chart(eventsCtx, eventsConfig);

let radarCtx = document.getElementById('radar-canvas').getContext('2d');
let radarChart = new Chart(radarCtx, radarConfig);
