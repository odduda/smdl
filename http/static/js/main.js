function dformat(str, ...arr) {
    return str.replace(/%(\d+)/g, function (_, i) {
        return arr[--i];
    });
}
function linkTo(path) {
    window.open(
        window.location.protocol + "//" + window.location.host + path,
        "_self"
    );
}
class SubmitButtonAnimation {
    // SPREMNO
    constructor(id) {
        this.id = "#" + id;
    }
    set progress(type) {
        switch (type) {
            case "loading":
                this.loading();
                break;
            case "done":
                this.done();
                break;
            case "fail":
                this.fail();
                break;
            default:
                setTimeout(() => {
                    this.reset();
                }, 1200);
                break;
        }
    }
    loading() {
        $(this.id).find("p").css({ opacity: "0" });
        $(this.id).addClass("sb-disable sb-loading");
    }
    done() {
        $(this.id).removeClass("sb-loading").addClass("sb-done");
        this.progress = "";
    }
    fail() {
        $(this.id).removeClass("sb-loading").addClass("sb-fail");
        this.progress = "";
    }
    reset() {
        $(this.id).removeClass("sb-disable sb-loading sb-done sb-fail");
        $(this.id).find("p").css({ opacity: "1" });
    }
}
class Notification {
    // SPREMNO
    constructor(id) {
        this.wrapper = document.getElementById(id);
        this.timeout = 5000;
    }

    addError(error) {
        switch (error.status) {
            case 0:
                this.addOne("Requested url is not reachable", "error");
                break;
            case 400:
            case 404:
                this.addMany(error.responseJSON, "error");
                break;
            case 500:
                this.addOne("Server Internal Error", "error");
                break;
            default:
                this.addOne("Client error", "error");
                break;
        }
    }

    addOne(msg, type) {
        let payload = (document.createElement("span").innerText = msg);
        this.appendMessage(payload, type);
    }
    addMany(array, type) {
        let payload = "";
        for (const msg of array) {
            payload += `<span>${msg}</span>`;
        }
        this.appendMessage(payload, type);
    }

    appendMessage(payload, type) {
        let div = document.createElement("div");
        div.className = type;
        div.innerHTML = payload;
        div.addEventListener("click", () => {
            div.remove();
        });
        setTimeout(() => {
            div.remove();
        }, this.timeout);
        this.wrapper.appendChild(div);
    }
}
class Graph {
    // SPREMNO
    constructor(div, type) {
        this.uplot = null;
        this.div = document.getElementById(div);
        this.type = type;
        this.settings = {
            csms: {
                lc_id: "csms_period",
                series: [
                    {},
                    {
                        show: true,
                        spanGaps: false,
                        label: "Moisture",
                        value: (self, rawValue) => rawValue + "%",
                        stroke: "rgba(0, 157, 223, 1)",
                        width: 1,
                        fill: "rgba(0, 157, 223, 0.3)",
                        dash: [10, 5],
                    },
                ],
                url: (params) => {
                    return dformat(
                        "/api/server/%1/csms/%2/chart/%3",
                        params.server_id,
                        params.csms_name,
                        this.period
                    );
                },
                restart: () => {
                    this.plot([[], []]);
                },
            },
            aht: {
                lc_id: "aht_period",
                series: [
                    {},
                    {
                        show: true,
                        spanGaps: false,
                        label: "Temperature",
                        value: (self, rawValue) => rawValue + "℃",
                        stroke: "rgba(255, 0, 0, 1)",
                        width: 1,
                        fill: "rgba(255, 0, 0, 0.3)",
                        dash: [10, 5],
                    },
                    {
                        show: true,
                        spanGaps: false,
                        label: "Humidity",
                        value: (self, rawValue) => rawValue + "%",
                        stroke: "rgba(0, 157, 223, 1)",
                        width: 1,
                        fill: "rgba(0, 157, 223, 0.3)",
                        dash: [10, 5],
                    },
                ],
                url: (params) => {
                    return dformat(
                        "/api/server/%1/aht/chart/%2",
                        params.server_id,
                        this.period
                    );
                },
                restart: () => {
                    this.plot([[], [], []]);
                },
            },
        };
    }

    set period(val) {
        localStorage.setItem(this.settings[this.type].lc_id, val);
    }

    get period() {
        let val = localStorage.getItem(this.settings[this.type].lc_id);
        return val ? val : "7";
    }

    fetchData(params) {
        $.ajax({
            url: this.settings[this.type].url(params),
            method: "GET",
        })
            .done((response) => {
                this.plot(response.data);
            })
            .fail((error) => {
                NOTIFY.addError(error);
                this.settings[this.type].restart();
            });
    }

    opts() {
        const data = {
            width: 800,
            height: 600,
            series: this.settings[this.type].series,
        };
        return data;
    }
    plot(data) {
        let opts = this.opts();
        if (this.uplot === null) {
            this.uplot = new uPlot(opts, data, this.div);
            return;
        }
        this.uplot.setData(data);
    }
}
class PotAnimation {
    constructor(id) {
        this.canvas = document.getElementById(id);
        this.ctx = this.canvas.getContext("2d");
        this.width = null;
        this.height = null;
        this.settings = {
            amount: 16,
            speed: 1.2,
            imgX: 45,
            imgY: 64,
            radius: 32,
        };
        this.pots = [];
        this.images = [];
        this.canvas.addEventListener("click", this.onClick.bind(this));
        window.addEventListener("resize", () => this.setCanvasSize());
        this.setCanvasSize();
        this.loadImages();
    }
    setCanvasSize() {
        this.width = this.canvas.parentNode.clientWidth;
        this.height = this.canvas.parentNode.clientHeight;
        this.canvas.setAttribute("width", this.width);
        this.canvas.setAttribute("height", this.height);
    }

    loadImages() {
        for (let i = 0; i < 6; i++) {
            let img = new Image(this.settings.imgX, this.settings.imgY);
            img.src =
                window.location.protocol +
                "//" +
                window.location.host +
                "/static/img/plant" +
                i +
                ".png";
            img.onload = () => {
                this.images.push(img);
            };
        }
        const interval = setInterval(() => {
            if (this.images.length === 6) {
                clearInterval(interval);
                this.createPots();
                this.animate();
            }
        }, 50);
    }

    onClick(e) {
        this.addOnePot(e.x - this.settings.imgX / 2, e.y - this.settings.imgY / 2);
    }

    addOnePot(cx = null, cy = null) {
        if (this.pots.length > 64) return;
        this.pots.push({
            x: cx ? cx : this.randomNumber(this.width),
            y: cy ? cy : this.randomNumber(this.height),
            angle: this.randomNumber(360),
            speed: this.randomNumber(3, 1),
            img: this.images[this.randomNumber(6)],
        });
    }

    createPots() {
        for (let i = this.pots.length; i < this.settings.amount; i++) {
            this.addOnePot();
        }
    }
    animate() {
        this.isOutOfBoundary();
        this.move();
        this.draw();
        window.requestAnimationFrame(this.animate.bind(this));
    }
    move() {
        for (const pot of this.pots) {
            pot.x += pot.speed * 1.2 * Math.cos(pot.angle);
            pot.y += pot.speed * 1.2 * Math.sin(pot.angle);
        }
    }
    draw() {
        this.ctx.clearRect(0, 0, this.width, this.height);
        for (const pot of this.pots) {
            this.ctx.drawImage(
                pot.img,
                pot.x,
                pot.y,
                this.settings.imgX,
                this.settings.imgY
            );
        }
    }

    isOutOfBoundary() {
        let safe = [];
        for (const pot of this.pots) {
            if (pot.x > this.width || pot.x < -this.settings.imgY) continue;
            if (pot.y > this.height || pot.y < -this.settings.imgY) continue;
            safe.push(pot);
        }
        this.pots = safe;
        this.createPots();
    }

    randomNumber(max, fromZero = 0) {
        return Math.floor(Math.random() * max) + fromZero;
    }
}
class ServerList {
    // SPREMNO !!!
    constructor() {
        this.data = [];
        this.current_page = 0;
        this.last_page = 0;
    }
    get() {
        $.ajax({
            url: "/api/server",
            method: "GET",
        })
            .done((data) => {
                if (data.length === 0) return;
                this.data = data;
                this.last_page = data.length;
                this.current_page = 1;
                this.update();
            })
            .fail((error) => NOTIFY.addError(error));
    }
    get id() {
        return this.data[this.current_page - 1]["id"];
    }
    prev() {
        this.change(this.current_page - 1);
    }
    next() {
        this.change(this.current_page + 1);
    }
    goto() {
        let val = parseInt($("#gotoInput").val());
        if (!isNaN(val)) {
            this.change(val);
        }
    }
    change(next) {
        if (next <= 0) return;
        if (next > this.last_page) return;
        this.current_page = next;
        this.update();
    }
    update() {
        let idx = this.current_page - 1;
        let tmp =
            this.data[idx]["tmp"] === null
                ? "- - . -"
                : Number(this.data[idx]["tmp"]).toFixed(1);
        let hum =
            this.data[idx]["hum"] === null
                ? "- -"
                : Number(this.data[idx]["hum"]).toFixed(1);
        $("#current").text(this.current_page);
        $("#max").text(this.last_page);
        $("#name").text(this.data[idx]["name"]);
        $("#temperature").text(tmp);
        $("#humidity").text(hum);
    }
}
class Server {
    constructor() {
        this.server_id = null;
        this.data = null;
        this.interval = 10;
    }
    set id(server_id) {
        this.server_id = server_id;
    }
    delete(e) {
        let confirm = parseInt($(e.target).attr("data-confirm"));
        if (!Boolean(confirm)) {
            $(e.target).text("Are you sure?");
            $(e.target).addClass("confirm");
            $(e.target).attr("data-confirm", 1);
            return
        }
        $.ajax({
            url: `/api/server/${this.server_id}/delete`,
            method: "GET"
        }).done((_) => {
            return linkTo("/");
        }).fail((error) => NOTIFY.addError(error));
    }
    getLatest() {
        if (this.server_id === null) {
            return NOTIFY.addOne("Server id is missing", "error");
        }
        $.ajax({
            url: `/api/server/${this.server_id}/latest`,
            method: "GET",
        })
            .done((response) => {
                this.data = response;
                if (Boolean(this.data.calibrate)) {
                    this.interval = 5;
                    return this.updateTmp();
                }
                this.interval = 30;
                return this.update();
            })
            .fail((error) => NOTIFY.addError(error));
    }
    update() {
        for (const [address, channels] of Object.entries(this.data.csms)) {
            for (const [channel, data] of Object.entries(channels)) {
                $(`#${address}-${channel}-value`).text(data.value);
                $(`#${address}-${channel}-valueCSS`).css({ height: `${data.value}%` });
                $(`#${address}-${channel}-calibrationDate`).text(data.calibration_date);
                $(`#${address}-${channel}-lastUpdated`).text(data.last_updated);
                $(`#${address}-${channel}-rawValue`).text(data.raw_value);
            }
        }
        $("#temperature").text(this.data.aht.temperature);
        $("#humidity").text(this.data.aht.humidity);
    }
    updateTmp() {
        for (const [address, channels] of Object.entries(this.data.csms)) {
            for (const [channel, data] of Object.entries(channels)) {
                $(`#${address}-${channel}-calibrationDate`).text(data.calibration_date);
                $(`#${address}-${channel}-rawValue`).text(data.raw_value);
            }
        }
    }
    setInputValue(id, type) {
        let value = $(`#${id}-rawValue`).text();
        $(`#${id}-input-${type}`).val(value);
    }
    updateCalibrationValue(id) {
        let min = $(`#${id}-input-min`).val();
        let max = $(`#${id}-input-max`).val();
        let name = id.replace("-", ":");
        let data = {
            min: min,
            max: max,
            name: name,
        };
        $.ajax({
            url: `/api/server/${this.server_id}/calibrate`,
            method: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
        })
            .done(() => {
                console.log("COMPLETE");
            })
            .fail((error) => NOTIFY.addError(error));
    }

    updateCalibrationState() {
        let toggle = Boolean(this.data.calibrate) ? 0 : 1;
        $.ajax({
            url: `/api/server/${this.server_id}/update-calibration/${toggle}`,
            method: "GET",
        })
            .done((_) => {
                this.data.calibrate = !this.data.calibrate;
                let calibrateText = Boolean(this.data.calibrate) ? "On" : "Off";
                $("#calibrateStatus").text(calibrateText);
                if (this.data.calibrate) {
                    $("#calibrateStatus").removeClass("Off").addClass("On");
                } else {
                    $("#calibrateStatus").removeClass("On").addClass("Off");
                }
            })
            .fail((error) => NOTIFY.addError(error));
        for (const [address, channels] of Object.entries(this.data.csms)) {
            for (const [channel, _] of Object.entries(channels)) {
                $(`#${address}-${channel}-showCalibrate`).toggleClass("hide");
            }
        }
    }
}
function cuForm(e, button, doneFN, url) {
    // Create Update Form for server
    e.preventDefault();
    let form = $(e.target).serializeArray();
    let data = {};
    $(form).each((_, obj) => {
        data[obj.name] = obj.value;
    });
    $.ajax({
        url: url,
        method: "POST",
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: "json",
    })
        .done((data) => doneFN(e, button, data))
        .fail((error) => {
            setTimeout(() => {
                $(e.target).trigger("reset");
                NOTIFY.addError(error);
                button.progress = "fail";
            }, 2000);
        });
}
const ROUTER = new Navigo("/");
const NOTIFY = new Notification("notification");
const SVL = new ServerList();
const SERVER = new Server();
ROUTER.on("/", function () {
    let _ = new PotAnimation("ca");
    $("#prev").on("click", () => {
        SVL.prev();
    });
    $("#next").on("click", () => {
        SVL.next();
    });
    $("#goto").on("click", () => {
        SVL.goto();
    });
    $("#gotoInput").on("keyup", (e) => {
        if (e.key === "Enter") {
            SVL.goto();
            e.target.select();
        }
    });
    $("#open").on("click", () => {
        if (SVL.id !== undefined) {
            window.open(window.location.href + "server/" + SVL.id, "_self");
        }
    });
    const doneForAddServer = (e, button, _response) => {
        setTimeout(() => {
            SVL.get();
            $(e.target).trigger("reset");
            button.progress = "done";
        }, 2000);
    };
    let button = new SubmitButtonAnimation("addServerSubmit");
    $("#add-server").on("submit", (e) => {
        cuForm(e, button, doneForAddServer, "/api/server");
    });
    $("#addServerSubmit").on("click", () => {
        button.progress = "loading";
        $("#add-server").submit();
    });
    SVL.get();
});
ROUTER.on("/server/:server_id", ({ data }) => {
    SERVER.id = data.server_id;
    $("#calibrate").on("click", () => {
        SERVER.updateCalibrationState();
    });
    const doneForUpdateServer = (_e, button, _response) => {
        setTimeout(() => {
            button.progress = "done";
        }, 2000);
    };
    let button = new SubmitButtonAnimation("updateServerSubmit");
    $("#update-server").on("submit", (e) => {
        cuForm(
            e,
            button,
            doneForUpdateServer,
            `/api/server/${data.server_id}/update`
        );
    });
    $("#updateServerSubmit").on("click", () => {
        button.progress = "loading";
        $("#update-server").submit();
    });
    $("#delete").on("click", (e) => {
        SERVER.delete(e)
    });
    const run = () => {
        SERVER.getLatest();
        setTimeout(run, SERVER.interval * 1000);
    }
    run();
});
ROUTER.on("/server/:server_id/csms/:csms_name", ({ data }) => {
    const graph = new Graph("graph", "csms");
    graph.fetchData(data);
    let select = $("#graphPeriod");
    select.val(graph.period);
    select.on("change", (e) => {
        graph.period = e.target.value;
        graph.fetchData(data);
    });
});
ROUTER.on("/server/:server_id/aht", ({ data }) => {
    const graph = new Graph("graph", "aht");
    graph.fetchData(data);
    let select = $("#graphPeriod");
    select.val(graph.period);
    select.on("change", (e) => {
        graph.period = e.target.value;
        graph.fetchData(data);
    });
});
ROUTER.on("*", () => {
    let _ = new PotAnimation("ca");
    console.log("ASDASDASDASD");
});
jQuery(function ($) {
    ROUTER.resolve();
});
