use chrono::Utc;
use chrono_tz::Tz;

const HELP: &str = "\
A utility to calculate the remaining time, in seconds, until the next execution of a cron
schedule. 

USAGE:
  next-wakeup --schedule '2,32 8-17 * * MON-FRI' --timezone 'Europe/Amsterdam'
  next-wakeup -s='2,32 8-17 * * MON-FRI' -tz='Europe/Amsterdam'

OPTIONS:
  -tz, --timezone STRING     Timezone used to interpret the cron schedule
  -s,  --schedule STRING     Cron schedule to calculate next wakeup
  -h,  --help                Prints help information
";

#[derive(Debug)]
struct Args {
    timezone: Tz,
    schedule: String,
}

fn main() {
    let args = match parse_args() {
        Ok(v) => v,
        Err(e) => {
            eprintln!("Error: {}.", e);
            std::process::exit(1);
        }
    };

    let schedule = args.schedule;

    if schedule.split_whitespace().count() < 5 {
        eprintln!("Error: Invalid cron schedule.");
        std::process::exit(1);
    }

    let now = Utc::now().with_timezone(&args.timezone);
    let next = match cron_parser::parse(&schedule, &now) {
        Ok(t) => t,
        Err(_) => {
            eprintln!("Error: Invalid cron schedule.");
            std::process::exit(1);
        }
    };

    let diff = next - now;

    println!("{}", diff.num_seconds());
}

fn parse_args() -> Result<Args, pico_args::Error> {
    let mut pargs = pico_args::Arguments::from_env();

    if pargs.contains(["-h", "--help"]) {
        print!("{}", HELP);
        std::process::exit(1);
    }

    let args = Args {
        timezone: pargs.value_from_str(["-tz", "--timezone"])?,
        schedule: pargs.value_from_str(["-s", "--schedule"])?
    };

    Ok(args)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    #[test]
    fn test_valid_cron_schedule() {
        let tz: Tz = "Europe/London".parse().unwrap();
        let now = tz.ymd(2023, 1, 1).and_hms(12, 0, 0);
        let schedule = "0 * * * *"; // Every hour
        
        let next = cron_parser::parse(schedule, &now).unwrap();
        assert_eq!(next, tz.ymd(2023, 1, 1).and_hms(13, 0, 0));
    }

    #[test]
    fn test_invalid_cron_schedule() {
        let tz: Tz = "UTC".parse().unwrap();
        let now = tz.ymd(2023, 1, 1).and_hms(12, 0, 0);
        let schedule = "a b c d e"; // Invalid format but 5 parts
        
        let result = cron_parser::parse(schedule, &now);
        assert!(result.is_err());
    }
}

