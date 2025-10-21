use criterion::{criterion_group, criterion_main, BatchSize, BenchmarkId, Criterion, Throughput};
use rustc_hash::FxHashSet;

type SpanKey = (usize, usize);

fn build_fixture(curr_len: usize, prev_len: usize) -> (Vec<SpanKey>, Vec<SpanKey>) {
    let mut previous = Vec::with_capacity(prev_len);
    for i in 0..prev_len {
        previous.push((i * 4, i * 4 + 1));
    }

    let mut current = Vec::with_capacity(curr_len);
    for i in 0..curr_len {
        if i % 11 == 0 && !previous.is_empty() {
            // Hit existing previous span.
            let key = previous[i % prev_len];
            current.push(key);
        } else if i % 7 == 0 && !current.is_empty() {
            // Repeat a seen key to exercise duplicate filtering.
            current.push(current.last().copied().unwrap());
        } else {
            let base = curr_len + i * 3;
            current.push((base, base + 1));
        }
    }

    (current, previous)
}

fn filter_with_fx(current: &[SpanKey], previous: &[SpanKey]) -> usize {
    let mut prev = FxHashSet::with_capacity_and_hasher(previous.len(), Default::default());
    for &key in previous {
        prev.insert(key);
    }
    let mut seen = FxHashSet::with_capacity_and_hasher(current.len(), Default::default());
    let mut filtered = 0usize;
    for &key in current {
        if prev.contains(&key) || !seen.insert(key) {
            continue;
        }
        filtered += 1;
    }
    filtered + previous.len()
}

fn bench_filter(c: &mut Criterion) {
    let mut group = c.benchmark_group("filter_previous_rule_same_span");

    for &(curr_len, prev_len) in &[(1_000, 1_000), (10_000, 5_000), (20_000, 10_000)] {
        group.throughput(Throughput::Elements(curr_len as u64));

        group.bench_with_input(
            BenchmarkId::new("fx_hashset", format!("{}-{}", curr_len, prev_len)),
            &(curr_len, prev_len),
            |b, &(curr, prev)| {
                b.iter_batched(
                    || build_fixture(curr, prev),
                    |(current, previous)| {
                        criterion::black_box(filter_with_fx(&current, &previous));
                    },
                    BatchSize::SmallInput,
                );
            },
        );
    }

    group.finish();
}

criterion_group!(benches, bench_filter);
criterion_main!(benches);
