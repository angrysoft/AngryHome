import 'dart:async';
import 'dart:html';
import 'dart:convert';
import 'package:service_worker/window.dart' as sw;
import '../lib/devicewidget.dart';

void _log(Object o) => print('  MAIN: $o');

class Page {
  Devices devices = new Devices();
  // Scenes scenes = new Scenes();
  EventSource events;

  Page() {
    HttpRequest.getString('/dev/data/all').then((String resp) {
      List<dynamic> jdata = jsonDecode(resp);
      jdata.forEach((dev) {
        this.devices.register(dev, print);
      });
    });

    HttpRequest.getString('/scene/list').then((String resp) {
      List<dynamic> jdata = jsonDecode(resp);
      jdata.forEach((dev) {
        dev['model'] = 'scene';
        this.devices.register(dev, print);
      });
    });
    
    this.events = new EventSource('/stream');
    this.events.onMessage.listen((ev) {
      this.devices.refresh(ev.data);
    });
    this.events.onOpen.listen((e){
      print('conn');
      print('${this.events.url} ${this.events.readyState}');
    });
    this.events.onError.listen((er){
      print('err ${er}');
    });

    document.onVisibilityChange.listen((event) {
      if (! document.hidden) {
        this.refreshStatus();
      }
    });

  }

  // TODO: check
  Future refreshStatus() async {
    HttpRequest.getString('/dev/data/all').then((String resp) {
      try {
        List<dynamic> jdata = jsonDecode(resp);
        jdata.forEach((dev) {
          this.devices.refresh(dev);
        });
      }
      on FormatException {
        print('Data pare err');
      }
    });
  }
}

class Tabs {
  num currentTab = 0;
  num lastTab;
  List<DivElement> tabs;
  bool _enable = true;
  DivElement tabContainer;

  Tabs() {
    this.tabs = querySelectorAll('.tab');
    this.tabContainer = querySelector('#tabs');
    this.lastTab = tabs.length - 1;

    Point tstart;
    Point tend;
    if (tabs.isNotEmpty) {
      this.currentTab = 0;

      if (window.localStorage.containsKey("currentTab")) {
        this.currentTab = int.parse(window.localStorage["currentTab"]);
      }

      this.changeTab(this.currentTab);
    }

    this.tabContainer.onTouchStart.listen((e) {
      tstart = new Point(e.touches[0].client.x, 0);
    });

    this.tabContainer.onTouchEnd.listen((e) {
      if (this.enableTouch) {
        tend = Point(e.changedTouches[0].client.x, 0);
        num move = tstart.x - tend.x;
        if (tend.distanceTo(tstart) > 100) {
          if (move > 0) {
            this.swipeLeft();
          } else {
            this.swipeRight();
          }
        }
      }
    });
  }

  bool get enableTouch {
    return this._enable;
  }

  void set enableTouch(bool value) {
    this._enable = value;
  }

  void swipeLeft() {
    num nextTab = this.currentTab + 1;
    if (this.lastTab >= nextTab) {
      this.changeTab(nextTab);
    } else {
      this.changeTab(0);
    }
  }

  void swipeRight() {
    num nextTab = this.currentTab - 1;
    if (nextTab >= 0) {
      this.changeTab(nextTab);
    } else {
      this.changeTab(this.lastTab);
    }
  }

  void changeTab(num tab) {
    List<Element> active = querySelectorAll('.active');
    active.forEach((a) {
      a.classes.remove('active');
    });
    tabs[tab].classes.add('active');
    this.currentTab = tab;
    window.localStorage['currentTab'] = this.currentTab.toString();
  }
}

Future main() async {
  new Page();
  new Tabs();

  if (sw.isNotSupported) {
    _log('ServiceWorkers are not supported.');
    return;
  }

  await sw.register('/static/devices/sw.dart.js');
  _log('registered');

  sw.ServiceWorkerRegistration registration = await sw.ready;
  _log('ready');

  sw.onMessage.listen((MessageEvent event) {
    _log('reply received: ${event.data}');
  });

  var message = 'Sample message: ${new DateTime.now()}';
  _log('Sending message: `$message`');
  registration.active.postMessage(message);
  _log('Message sent: `$message`');

  try {
    var subs = await registration.pushManager
        .subscribe(new sw.PushSubscriptionOptions(userVisibleOnly: true));
    _log('endpoint: ${subs.endpoint}');
  } on DomException catch (e) {
    _log('Error: Adding push subscription failed. ${e}');
    _log('       See github.com/isoos/service_worker/issues/10');
  }
}
