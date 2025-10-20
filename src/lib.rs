use fast_bunkai_rs::{
    segment as segment_core, segment_boundaries as segment_boundaries_core, Segmentation,
};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

fn segmentation_to_py(py: Python<'_>, output: &Segmentation) -> PyResult<PyObject> {
    let dict = PyDict::new_bound(py);
    let layers = PyList::empty_bound(py);
    for layer in &output.layers {
        let layer_dict = PyDict::new_bound(py);
        layer_dict.set_item("name", layer.name)?;
        let spans_list = PyList::empty_bound(py);
        for span in &layer.spans {
            let span_dict = PyDict::new_bound(py);
            span_dict.set_item("rule_name", span.rule_name)?;
            span_dict.set_item("start", span.start)?;
            span_dict.set_item("end", span.end)?;
            match span.split_type {
                Some(value) => span_dict.set_item("split_type", value)?,
                None => span_dict.set_item("split_type", py.None())?,
            }
            match &span.split_value {
                Some(value) => span_dict.set_item("split_value", value)?,
                None => span_dict.set_item("split_value", py.None())?,
            }
            spans_list.append(&span_dict)?;
        }
        layer_dict.set_item("spans", &spans_list)?;
        layers.append(&layer_dict)?;
    }
    dict.set_item("layers", &layers)?;
    dict.set_item("final_boundaries", output.final_boundaries.clone())?;
    Ok(dict.into_py(py))
}

#[allow(clippy::useless_conversion)]
#[pyfunction]
fn segment(py: Python<'_>, text: &str) -> PyResult<PyObject> {
    let output = py.allow_threads(|| segment_core(text));
    segmentation_to_py(py, &output)
}

#[pyfunction]
fn segment_boundaries(py: Python<'_>, text: &str) -> PyResult<Vec<usize>> {
    let boundaries = py.allow_threads(|| segment_boundaries_core(text));
    Ok(boundaries)
}

#[pymodule]
fn _fast_bunkai(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(segment, m)?)?;
    m.add_function(wrap_pyfunction!(segment_boundaries, m)?)?;
    Ok(())
}
