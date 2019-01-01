
let WEB_URL = window.location.origin;

$(document).ready(() => {
  setInterval(() => {
    fetch(WEB_URL + '/update', {
        method: "GET"
    })
    .then(response => response.json())
    .then(updated => {
      console.log(updated);
      onRootUpdate(updated);
    });
  }, 500);
});

function send(subject, data) {
  fetch(WEB_URL + '/data/' + subject, {
      method: "POST",
      cache: "no-cache",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(json => {
    console.log(json);
    if(json.alert) {
      alert(json.alert);
    }
  });
}
