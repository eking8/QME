"""
fritz.api_resources.model_grade_report
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2020 by Fritz Labs Incorporated
:license: MIT, see LICENSE for more details.
"""
from termcolor import colored

import fritz
from fritz.api_resources import fritz_object
from fritz.api_client import FritzClient


class ModelGradeReport(fritz_object.FritzObject):
    """Model Benchmark report."""

    OBJECT_NAME = "ModelGradeReport"

    @classmethod
    def get(cls, api_key=None, version_id=None):
        """Get model grade report for version_id

        Args:
            version_id (str): ID of ModelVersion
            api_key (str): Optional API Key

        Returns: ModelGradeReport if report has succeeded.
        """
        url = "/model/version/{version_id}/grader".format(version_id=version_id)

        client = FritzClient(api_key or fritz.api_key)
        response = client.get(url)
        return fritz.utils.convert_to_fritz_object(response)

    def summary(self):
        """Print summary of model grade report."""
        if self.fail_at:
            self._error_summary()
            return

        self.layer_summary()

        stats = []
        # Check Core ML Compatibility
        incompatible_layers = [
            layer for layer in self.layers if not layer["is_coremltools_compatible"]
        ]
        compatible = len(incompatible_layers) == 0
        color = "green" if compatible else "red"
        stats.append(("Core ML Compatible", colored(str(compatible), color)))

        # Calculate Predicted Runtime
        if self.predicted_runtime < 1.0:
            runtime = "{predicted_runtime:.1f} ms".format(
                predicted_runtime=self.predicted_runtime * 1000
            )
        else:
            runtime = "{predicted_runtime:.3}s".format(
                predicted_runtime=self.predicted_runtime
            )

        runtime = "{runtime} ({fps:,.1f} fps)".format(
            runtime=runtime, fps=1 / self.predicted_runtime
        )
        stats.append(("Predicted Runtime (iPhone X)", runtime))

        # FLOPS, Parameters, Version ID.
        stats.append(
            (
                "Total MFLOPS",
                "{mflops:,.2f}".format(mflops=self.total_flops / 1.0e6),
            )
        )
        stats.append(
            (
                "Total Parameters",
                "{total_parameters:,d}".format(total_parameters=self.total_parameters),
            )
        )
        stats.append(("Fritz Version ID", self.version_id))

        max_title_length = max(len(title) for title, _ in stats)
        summary_str = "Fritz Model Grade Report"
        print("\n" + "-" * len(summary_str))
        print(summary_str)
        print("-" * len(summary_str) + "\n")
        for title, value in stats:
            title = title + ":"
            format_str = "{title:%s}{value}" % str(max_title_length + 5)
            print(format_str.format(title=title, value=value))

    def layer_summary(self):
        """Print summary of layers from report."""
        summary_str = "Model Layer Summary"
        print("\n" + "-" * len(summary_str))
        print(summary_str)
        print("-" * len(summary_str) + "\n")

        layers = [
            (
                "Layer (type)",
                "Output Shape",
                "MFLOPS",
                "Weights",
                "Core ML Compatible",
            )
        ]
        layers.extend(self._summarize_layer(layer) for layer in self.layers)
        max_lengths = [max(len(value) for value in values) for values in zip(*layers)]
        for i, fields in enumerate(layers):
            line = []
            for j, field in enumerate(fields):
                format_str = "{value:%s}" % str(max_lengths[j] + 5)
                line.append(format_str.format(value=str(field)))

            line_length = len("".join(line))

            if i == 0:
                print("-" * line_length)
                print("".join(line))
                print("=" * line_length)
            else:
                print("".join(line))
                print("-" * line_length)

    @staticmethod
    def _summarize_layer(layer):
        layer_type = layer["name"] + " (" + layer["layer_cls_name"] + ")"
        output_shape = layer["output_shape"]
        mflops = "{mflops:,.2f}".format(mflops=layer["flops"] / 1.0e6)
        weights = "{num_weights:,d}".format(num_weights=layer["num_weights"])
        color = "green" if layer["is_coremltools_compatible"] else "red"
        compatible = colored(layer["is_coremltools_compatible"], color)

        return (layer_type, output_shape, mflops, weights, compatible)

    def _error_summary(self):
        message = "Model Grade Report Failed"
        print(colored(message, "red"))
        print(colored("-" * len(message), "red"))
        print("Error Message: " + self.error_message)
