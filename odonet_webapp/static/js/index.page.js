/*
Main Dashboard Page
*/

function onRootUpdate(updated) {

  for(let key of Object.keys(updated)) {

    if(key.startsWith('node_')) {
      let node = key.slice(5);
      let updatedData = updated[key];
      for(let cam = 0; cam < 6; cam++) {
        if(updatedData['current_image_' + cam]) {
          $('#current-image-' + node + '-' + cam).attr('src', '/files/' + updatedData['current_image_' + cam]);
        }
      }
      if(updatedData['last_updated']) {
        $('#last-packet-' + node).html(updated[key]['last_updated']);
      }
    }

  }

  if(updated.page) {
    window.location.reload();
  }

}

function onRouteClick(device) {
  let btn = $('#route-btn-' + device);
  let group = $('#route-group-' + device);
  let text = $('#route-text-' + device);
  btn.toggleClass('btn-danger');
  btn.toggleClass('btn-outline-success');
  if(btn.html() == 'Routing') {
    btn.html('Save Route');
    group.show();
  } else {
    btn.html('Route (Edited)');
    group.hide();
    send('route', {id: device, route: text.val()});
  }
}

function onShellClick(device) {
  let btn = $('#shell-btn-' + device);
  let group = $('#shell-group-' + device);
  let text = $('#shell-text-' + device);
  btn.toggleClass('btn-light');
  btn.toggleClass('btn-outline-success');
  if(btn.html() == 'Shell') {
    btn.html('Run Shell');
    group.show();
  } else {
    btn.html('Shell');
    group.hide();
    send('shell', {id: device, script: text.val()});
    text.val('');
  }
}

function onConfigClick(device) {
  let btn = $('#config-btn-' + device);
  let group = $('#config-group-' + device);
  let text = $('#config-text-' + device);
  btn.toggleClass('btn-primary');
  btn.toggleClass('btn-outline-success');
  if(btn.html() == 'Config') {
    btn.html('Save Config');
    group.show();
  } else {
    btn.html('Config');
    group.hide();
    send('config', {id: device, conf: JSON.parse(text.val())});
  }
}
