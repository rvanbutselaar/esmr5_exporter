import logging
import time
import os

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily
from smeterd.meter import SmartMeter

"""
Inspired by:
* https://github.com/sanderjo/P1/blob/master/P1-parser.awk
* https://github.com/prometheus/client_python
* https://github.com/gejanssen/slimmemeter-rpi
* http://domoticx.com/p1-poort-slimme-meter-hardware/
* https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_a727fce1f1.pdf

'1-0:1.8.1':'p1_total_electricity_used_rate_1',
'1-0:1.8.2':'p1_total_electricity_used_rate_2',
'1-0:2.8.1':'p1_total_electricity_provided_rate_1',
'1-0:2.8.2':'p1_total_electricity_provided_rate_2',
'1-0:1.7.0':'p1_total_electricity_used',
'1-0:2.7.0':'p1_total_electricity_provided',
'1-0:32.7.0':'p1_l1_voltage',
'1-0:52.7.0':'p1_l2_voltage',
'1-0:72.7.0':'p1_l3_voltage',
'0-0:96.14.0':'p1_current_tarrif' ( 2 is high)
"""


def markup_helper(str_line):
    """
    Read raw string and return only the value
    """
    return int(str_line.split("(")[-1].split("*")[0].replace(".", ""))


def markup_helper_float(str_line):
    """
    Read raw string and return only the value for Floating Point Numbers (Floats)
    """
    return float(str_line.split("(")[-1].split("*")[0])


def markup_helper_tarrif(str_line):
    """
    Read raw string and return only the value for Tarrif
    """
    return int(str_line.split("(")[-1].replace(")", "").replace("0", ""))


def metric_helper(metric_name, p1_line, metrics):
    """
    Create a metric object
    """
    logging.debug(f"{ metric_name }: { p1_line }")
    metrics[metric_name].add_metric(["Rozensingel"], markup_helper(p1_line))

    return metrics


def metric_helper_float(metric_name, p1_line, metrics):
    """
    Create a metric object for Floating Point Numbers (Floats)

    """
    logging.debug(f"{ metric_name }: { p1_line }")
    metrics[metric_name].add_metric(["Rozensingel"], markup_helper_float(p1_line))

    return metrics


def metric_helper_tarrif(metric_name, p1_line, metrics):
    """
    Create a metric object for Tarrif
    """
    logging.debug(f"{ metric_name }: { p1_line }")
    metrics[metric_name].add_metric(["Rozensingel"], markup_helper_tarrif(p1_line))

    return metrics


class CustomCollector(object):
    def get_p1_metrics(self, p1_lines, metrics):
        # Convert to a list for simple parsing
        p1_list = str(p1_lines).splitlines()

        for p1_line in p1_list:
            # Meter Reading electricity delivered to client (low tariff) in 0,001 kWh
            if "1-0:1.8.1" in p1_line:
                metric_helper_float(
                    "p1_total_electricity_used_rate_1", p1_line, metrics
                )
            # Meter Reading electricity delivered to client (normal tariff) in 0,001 kWh
            elif "1-0:1.8.2" in p1_line:
                metric_helper_float(
                    "p1_total_electricity_used_rate_2", p1_line, metrics
                )
            # Meter Reading electricity delivered by client (low tariff) in 0,001 kWh
            elif "1-0:2.8.1" in p1_line:
                metric_helper_float(
                    "p1_total_electricity_provided_rate_1", p1_line, metrics
                )
            # Meter Reading electricity delivered by client (normal tariff) in 0,001 kWh
            elif "1-0:2.8.2" in p1_line:
                metric_helper_float(
                    "p1_total_electricity_provided_rate_2", p1_line, metrics
                )
            # Actual electricity power delivered (+P) in 1 Watt resolution
            elif "1-0:1.7.0" in p1_line:
                metric_helper("p1_electricity_used", p1_line, metrics)
            # Actual electricity power received (-P) in 1 Watt resolution
            elif "1-0:2.7.0" in p1_line:
                metric_helper("p1_electricity_provided", p1_line, metrics)
            # Instantaneous voltage L1
            elif "1-0:32.7.0" in p1_line:
                metric_helper_float("p1_l1_voltage", p1_line, metrics)
            # Instantaneous voltage L2
            elif "1-0:52.7.0" in p1_line:
                metric_helper_float("p1_l2_voltage", p1_line, metrics)
            # Instantaneous voltage L3
            elif "1-0:72.7.0" in p1_line:
                metric_helper_float("p1_l3_voltage", p1_line, metrics)
            # Tariff indicator electricity
            elif "0-0:96.14.0" in p1_line:
                metric_helper_tarrif("p1_current_tarrif", p1_line, metrics)
            # Instantaneous current L1 in A resolution
            elif "1-0:31.7.0" in p1_line:
                metric_helper_float("p1_l1_current", p1_line, metrics)
            # Instantaneous current L2 in A resolution
            elif "1-0:51.7.0" in p1_line:
                metric_helper_float("p1_l2_current", p1_line, metrics)
            # Instantaneous current L3 in A resolution
            elif "1-0:71.7.0" in p1_line:
                metric_helper_float("p1_l3_current", p1_line, metrics)
            # Number of power failures in any phase
            elif "0-0:96.7.21" in p1_line:
                metric_helper_tarrif("p1_power_failures", p1_line, metrics)
            # Instantaneous active power L1 (+P) in W resolution
            if "1-0:21.7.0" in p1_line:
                metric_helper("p1_l1_active_power_used", p1_line, metrics)
            # Instantaneous active power L2 (+P) in W resolution
            if "1-0:41.7.0" in p1_line:
                metric_helper("p1_l2_active_power_used", p1_line, metrics)
            # Instantaneous active power L3 (+P) in W resolution
            if "1-0:61.7.0" in p1_line:
                metric_helper("p1_l3_active_power_used", p1_line, metrics)
            # Instantaneous active power L1 (-P) in W resolution
            if "1-0:22.7.0" in p1_line:
                metric_helper("p1_l1_active_power_provided", p1_line, metrics)
            # Instantaneous active power L2 (-P) in W resolution
            if "1-0:42.7.0" in p1_line:
                metric_helper("p1_l2_active_power_provided", p1_line, metrics)
            # Instantaneous active power L3 (-P) in W resolution
            if "1-0:62.7.0" in p1_line:
                metric_helper("p1_l3_active_power_provided", p1_line, metrics)

        return metrics

    def collect(self):
        metrics = {
            "p1_total_electricity_used_rate_1": GaugeMetricFamily(
                "p1_total_electricity_used_rate_1",
                "Meter Reading electricity delivered to client (low tariff) in 0,001 kWh",
            ),
            "p1_total_electricity_used_rate_2": GaugeMetricFamily(
                "p1_total_electricity_used_rate_2",
                "Meter Reading electricity delivered to client (normal tariff) in 0,001 kWh",
            ),
            "p1_total_electricity_provided_rate_1": GaugeMetricFamily(
                "p1_total_electricity_provided_rate_1",
                "Meter Reading electricity delivered by client (low tariff) in 0,001 kWh",
            ),
            "p1_total_electricity_provided_rate_2": GaugeMetricFamily(
                "p1_total_electricity_provided_rate_2",
                "Meter Reading electricity delivered by client (normal tariff) in 0,001 kWh",
            ),
            "p1_electricity_used": GaugeMetricFamily(
                "p1_electricity_used",
                "Actual electricity power delivered (+P) in 1 Watt resolution",
            ),
            "p1_electricity_provided": GaugeMetricFamily(
                "p1_electricity_provided",
                "Actual electricity power received (-P) in 1 Watt resolution",
            ),
            "p1_l1_voltage": GaugeMetricFamily(
                "p1_l1_voltage", "Instantaneous voltage L1"
            ),
            "p1_l2_voltage": GaugeMetricFamily(
                "p1_l2_voltage", "Instantaneous voltage L3"
            ),
            "p1_l3_voltage": GaugeMetricFamily(
                "p1_l3_voltage", "Instantaneous voltage L3"
            ),
            "p1_current_tarrif": GaugeMetricFamily(
                "p1_current_tarrif", "Tariff indicator electricity"
            ),
            "p1_l1_current": GaugeMetricFamily(
                "p1_l1_current", "Instantaneous current L1 in A resolution"
            ),
            "p1_l2_current": GaugeMetricFamily(
                "p1_l2_current", "Instantaneous current L2 in A resolution"
            ),
            "p1_l3_current": GaugeMetricFamily(
                "p1_l3_current", "Instantaneous current L3 in A resolution"
            ),
            "p1_power_failures": GaugeMetricFamily(
                "p1_power_failures", "Number of power failures in any phase"
            ),
            "p1_l1_active_power_used": GaugeMetricFamily(
                "p1_l1_active_power_used",
                "Instantaneous active power L1 (+P) in W resolution",
            ),
            "p1_l2_active_power_used": GaugeMetricFamily(
                "p1_l2_active_power_used",
                "Instantaneous active power L2 (+P) in W resolution",
            ),
            "p1_l3_active_power_used": GaugeMetricFamily(
                "p1_l3_active_power_used",
                "Instantaneous active power L3 (+P) in W resolution",
            ),
            "p1_l1_active_power_provided": GaugeMetricFamily(
                "p1_l1_active_power_provided",
                "Instantaneous active power L1 (-P) in W resolution",
            ),
            "p1_l2_active_power_provided": GaugeMetricFamily(
                "p1_l2_active_power_provided",
                "Instantaneous active power L2 (-P) in W resolution",
            ),
            "p1_l3_active_power_provided": GaugeMetricFamily(
                "p1_l3_active_power_provided",
                "Instantaneous active power L3 (-P) in W resolution",
            ),
        }

        meter = SmartMeter("/dev/ttyUSB0", baudrate=115200)
        metrics = self.get_p1_metrics(meter.read_one_packet(), metrics)
        meter.disconnect()

        for metric in metrics.values():
            yield metric


if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=LOGLEVEL
    )
    logging.info("Starting ESMR5 metrics exporter")

    REGISTRY.register(CustomCollector())
    start_http_server(8000)

    while True:
        time.sleep(60)
