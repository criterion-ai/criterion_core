import altair as alt
import pandas as pd
import numpy as np


def make_selector_chart(df, x_name, y_name, selector, color="red", size=100):
    chart_line = alt.Chart(df).mark_line().encode(
        x=x_name,
        y=y_name)
    chart_sel = alt.Chart(df).mark_circle(color=color, size=size).encode(
        x=x_name,
        y=y_name).add_selection(selector).transform_filter(selector)
    chart_layered = alt.layer(chart_line, chart_sel)
    return chart_layered


def make_security_selection(devel_pred_output, classes):
    step = 1
    rng = np.arange(0.0, 100+step, step)

    security_charts = []
    for cl in classes:
        sec_level = '{}_security_level'.format(cl)
        slider = alt.binding_range(min=rng.min(), max=rng.max(), step=step)
        select_security = alt.selection_single(name="set", fields=[sec_level], bind=slider)
        scores_accept = np.array([sc["prob_" + cl] for sc in devel_pred_output if cl in sc["category"]])
        scores_reject = np.array([sc["prob_" + cl] for sc in devel_pred_output if not cl in sc["category"]])

        FRR = [(scores_accept < thr/100).sum()/len(scores_accept ) for thr in rng]
        TRR = [(scores_reject < thr/100).sum()/len(scores_reject) for thr in rng]

        ROC_df = pd.DataFrame({'FRR': FRR, 'TRR': TRR+1e-5*rng, sec_level: rng})


        ROC_comb_alt = make_selector_chart(df=ROC_df, x_name='TRR', y_name='FRR', selector=select_security)
        FRR_comb_alt = make_selector_chart(df=ROC_df, x_name=sec_level, y_name='FRR', selector=select_security)
        TRR_comb_alt = make_selector_chart(df=ROC_df, x_name=sec_level, y_name='TRR', selector=select_security)

        security_charts.append(alt.concat(ROC_comb_alt, FRR_comb_alt, TRR_comb_alt).resolve_scale(color='independent').to_json())
    return security_charts


def dataset_summary(samples):
    data = pd.DataFrame(list(samples))
    data["category"] = data["category"].apply(lambda x: x if isinstance(x, str) else "/".join(x))

    data = data.groupby(["dataset", "category"]) \
        .size().reset_index(name="samples")

    chart = alt.Chart(data) \
        .mark_bar() \
        .encode(x='samples',
                y='dataset',
                color='category',
                order=alt.Order(
                    'category',
                    sort='ascending'
                )) \
        .configure_axis(labelLimit=30)

    return chart.to_json()

if __name__ == "__main__":
    from criterion_core import load_image_datasets
    from criterion_core.utils import sampletools

    datasets = [
        dict(bucket=r'C:\data\novo\data\22df6831-5de9-4545-af17-cdfe2e8b2049.datasets.criterion.ai',
             id='22df6831-5de9-4545-af17-cdfe2e8b2049',
             name='test')
    ]

    dssamples = load_image_datasets(datasets)

    samples = list(sampletools.flatten_dataset(dssamples))

    vegalite_json = dataset_summary(samples)