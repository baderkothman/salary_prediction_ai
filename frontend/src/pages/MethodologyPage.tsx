import { ErrorState } from "../components/ErrorState";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { PageContainer, PageHeader } from "../components/PageContainer";
import { formatCurrency, formatDateTime } from "../lib/format";
import { useLatestPublishedRun } from "../lib/queries";

export function MethodologyPage() {
  const runQuery = useLatestPublishedRun();

  return (
    <PageContainer>
      <PageHeader title="Methodology" description="How a prediction gets from raw data to this dashboard." />

      <article className="methodology">
        <section>
          <h2>Dataset</h2>
          <p>
            Source: Kaggle <em>Data Science Job Salaries</em> dataset (
            <code>ruchi798/data-science-job-salaries</code>), 607 raw rows covering data-science roles from 2020–2022.
          </p>
        </section>

        <section>
          <h2>Cleaning</h2>
          <p>
            42 exact duplicate rows (once a meaningless row-index column is dropped) are removed and logged, not silently
            discarded. The dataset has zero missing values across all columns. Raw salary and salary-currency columns are
            excluded from the feature set entirely — combined with an implicit exchange rate, they would let the model
            reconstruct the target directly instead of learning from job/experience/location signal.
          </p>
        </section>

        <section>
          <h2>Features</h2>
          <p>
            Experience level, employment type, job title, employee residence, remote ratio, company location, and company
            size feed a <code>OneHotEncoder(handle_unknown="ignore")</code> for categoricals and a numeric passthrough for
            work year and remote ratio, wrapped in one scikit-learn <code>Pipeline</code> together with the model so
            preprocessing can never drift out of sync with it.
          </p>
        </section>

        <section>
          <h2>Model</h2>
          <p>
            A <code>DecisionTreeRegressor</code>, with hyperparameters (<code>max_depth</code>, <code>min_samples_split</code>,{" "}
            <code>min_samples_leaf</code>) chosen via 5-fold cross-validation on the training split only, then evaluated once
            on a held-out test set.
          </p>
          {runQuery.isPending && <LoadingSkeleton height={20} width="50%" />}
          {runQuery.isError && <ErrorState message="Could not load current model metrics." />}
          {runQuery.data && (
            <p>
              Current model <strong>{runQuery.data.model_version}</strong>, evaluated {formatDateTime(runQuery.data.created_at)}: MAE{" "}
              {formatCurrency(runQuery.data.model_metrics.mae)}, RMSE {formatCurrency(runQuery.data.model_metrics.rmse)}, R²{" "}
              {runQuery.data.model_metrics.r2.toFixed(2)}.
            </p>
          )}
        </section>

        <section>
          <h2>Input-space coverage</h2>
          <p>
            The generation pipeline calls the prediction API once for every <em>distinct observed</em> feature combination in
            the cleaned dataset — not a naive Cartesian product of every category, which would fabricate combinations that
            never occurred in practice.
          </p>
        </section>

        <section>
          <h2>How the narrative is grounded</h2>
          <p>
            A local Ollama model never calculates statistics itself. Python first computes the peer group's sample size,
            mean, median, and quartiles, plus the prediction's percentile rank in the full dataset; the LLM only explains
            those precomputed facts and is instructed to distinguish association from causation. Its JSON output is schema-
            validated before storage — malformed generations are retried, and persistently invalid ones are marked failed
            rather than stored. Because a local model's inference is relatively slow, only a fixed, reproducible sample of
            predictions receives a full narrative; every distinct combination still receives a direct model prediction.
          </p>
        </section>

        <section>
          <h2>Why this dashboard reads from a database instead of predicting live</h2>
          <p>
            Predictions and narratives are generated once by a local pipeline and published to this database only after
            passing a completeness check. This page — and every page here — reads only published data and never calls the
            prediction API or the LLM directly, so it stays fast and available even if the local generation pipeline isn't
            running.
          </p>
        </section>

        <section>
          <h2>Limitations</h2>
          <ul>
            <li>Predictions are estimates from historical, self-reported data, not compensation guarantees.</li>
            <li>Some detailed job/location combinations occurred too rarely in training data to predict confidently.</li>
            <li>The dataset shows associations between attributes and salary, not causal relationships.</li>
            <li>Only a sample of predictions received a full narrative, for local-inference-time reasons explained above.</li>
          </ul>
        </section>
      </article>
    </PageContainer>
  );
}
