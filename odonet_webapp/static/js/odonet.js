/*
OdoNet Functions
*/

let WEB_URL = window.location.origin;

$(document).ready(() => {

  // Poll the server for updates
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

/* Send a msg to the OdoNet server */
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


/* Calculate the average of the array */
function average(nums) {
  if(nums.length == 0) {
    return 0;
  }
  let sum = 0;
  for(let n of nums) {
    sum += n;
  }
  return sum / nums.length;
}
